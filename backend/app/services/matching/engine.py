import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from app.models import (
    CampaignProfile, MatchingRun, MatchResult, 
    PublisherRecord, PublisherObservation, Company
)

class MatchingEngine:
    SCORING_MODEL_VERSION = "1.0.0"

    def __init__(self, session: AsyncSession):
        self.session = session

    async def run_matching(self, company_id: uuid.UUID) -> MatchingRun:
        # Load Campaign Profile
        profile_result = await self.session.execute(
            select(CampaignProfile).where(CampaignProfile.company_id == company_id)
        )
        profile = profile_result.scalar_one_or_none()
        if not profile:
            # Auto-assemble campaign profile from company data
            company = await self.session.get(Company, company_id)
            if not company:
                raise ValueError("Company not found")
            profile = CampaignProfile(
                company_id=company_id,
                target_geography=company.country or "Global",
                target_industry=company.industry or "Technology",
                target_audience="General",
                topics=[company.industry] if company.industry else ["General"],
                max_budget=5000.0,
                budget_currency="USD",
                campaign_objective="Brand Awareness & SEO"
            )
            self.session.add(profile)
            await self.session.flush()

        # Create Run
        run = MatchingRun(
            company_id=company_id,
            profile_snapshot={
                "target_geography": profile.target_geography,
                "target_industry": profile.target_industry,
                "target_audience": profile.target_audience,
                "topics": profile.topics,
                "max_budget": profile.max_budget,
                "budget_currency": profile.budget_currency,
                "campaign_objective": profile.campaign_objective,
                "mandatory_constraints": profile.mandatory_constraints
            },
            scoring_model_version=self.SCORING_MODEL_VERSION,
            status="RUNNING"
        )
        self.session.add(run)
        await self.session.flush()

        try:
            # Load all active publishers with their latest observations
            publisher_results = await self.session.execute(
                select(PublisherRecord, PublisherObservation)
                .join(PublisherObservation, PublisherObservation.publisher_id == PublisherRecord.id)
                .order_by(PublisherObservation.observation_timestamp.desc())
            )
            
            # Deduplicate observations (take latest per publisher)
            publishers_dict = {}
            for pub, obs in publisher_results:
                if pub.id not in publishers_dict:
                    publishers_dict[pub.id] = (pub, obs)

            eligible_publishers = list(publishers_dict.values())
            
            # Constraints
            max_budget = profile.max_budget
            target_geo = profile.target_geography
            
            total_eligible = 0
            total_excluded = 0

            for pub, obs in eligible_publishers:
                # Apply hard exclusions
                if max_budget and obs.price and obs.price > max_budget:
                    total_excluded += 1
                    continue
                
                # Assume pub fits basic constraints if no explicit block
                total_eligible += 1
                
                # Calculate scores
                score, comp_scores, reasons, warnings = self._calculate_score(profile, pub, obs)
                
                result = MatchResult(
                    matching_run_id=run.id,
                    publisher_id=pub.id,
                    overall_score=score,
                    rank=0, # Will update after sorting
                    component_scores=comp_scores,
                    reasons=reasons,
                    warnings=warnings
                )
                self.session.add(result)
            
            # Finalize run
            run.total_eligible = total_eligible
            run.total_excluded = total_excluded
            run.status = "COMPLETED"
            
            await self.session.flush()
            
            # Update Ranks
            all_results = await self.session.execute(
                select(MatchResult)
                .where(MatchResult.matching_run_id == run.id)
                .order_by(MatchResult.overall_score.desc())
            )
            
            rank = 1
            for r in all_results.scalars():
                r.rank = rank
                rank += 1
                
            await self.session.commit()
            return run
            
        except Exception as e:
            run.status = "FAILED"
            run.error_message = str(e)
            await self.session.commit()
            raise e

    def _calculate_score(self, profile: CampaignProfile, pub: PublisherRecord, obs: PublisherObservation) -> tuple:
        reasons = []
        warnings = []
        comp_scores = {
            "topical_relevance": 0.0,
            "audience_alignment": 0.0,
            "geographic_relevance": 0.0,
            "publisher_quality": 0.0,
            "price_fit": 0.0,
            "editorial_suitability": 0.0
        }
        
        # Topical (35%)
        # Basic exact match string fallback
        if profile.target_industry and pub.audience_focus and profile.target_industry.lower() in pub.audience_focus.lower():
            comp_scores["topical_relevance"] = 35.0
            reasons.append({"factor": "topical", "evidence": f"Publisher audience focus '{pub.audience_focus}' matches target industry '{profile.target_industry}'"})
        else:
            comp_scores["topical_relevance"] = 15.0 # baseline
            
        # Geographic (10%)
        if profile.target_geography:
            # We don't have explicit geo in publisher, simulate missing
            comp_scores["geographic_relevance"] = 5.0
            warnings.append("Publisher geographic distribution is unverified.")
        else:
            comp_scores["geographic_relevance"] = 10.0 # N/A preference

        # Quality (15%)
        if obs.metric_da:
            q_score = (obs.metric_da / 100.0) * 15.0
            comp_scores["publisher_quality"] = q_score
            reasons.append({"factor": "quality", "evidence": f"Domain Authority is {obs.metric_da}"})
        elif obs.metric_dr:
            q_score = (obs.metric_dr / 100.0) * 15.0
            comp_scores["publisher_quality"] = q_score
            reasons.append({"factor": "quality", "evidence": f"Domain Rating is {obs.metric_dr}"})
        else:
            warnings.append("No authority metrics available.")

        # Price Fit (10%)
        if obs.price and profile.max_budget:
            ratio = obs.price / profile.max_budget
            if ratio < 0.5:
                comp_scores["price_fit"] = 10.0
                reasons.append({"factor": "price", "evidence": "Highly cost effective within budget"})
            elif ratio <= 1.0:
                comp_scores["price_fit"] = 5.0
                reasons.append({"factor": "price", "evidence": "Fits within budget"})
        else:
            comp_scores["price_fit"] = 5.0
            if not obs.price:
                warnings.append("Publisher price is unknown.")

        # Data Quality & Freshness Guardrails (Phase 3.1)
        # Check verification status
        if getattr(obs, "verification_status", None) == "UNVERIFIED":
            warnings.append("Publisher data is unverified (imported without third-party provider or human verification).")

        # Check freshness
        obs_time = obs.observation_timestamp
        if obs_time:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            if obs_time.tzinfo is None:
                obs_time = obs_time.replace(tzinfo=timezone.utc)
            age_days = (now - obs_time).days
            if age_days > 60:
                warnings.append(f"Publisher metrics are stale ({age_days} days old). Re-verification recommended prior to booking.")
            if obs.price and age_days > 30:
                warnings.append(f"Publisher pricing may be stale ({age_days} days old). Confirm rate card with media kit.")

        overall = sum(comp_scores.values())
        return overall, comp_scores, reasons, warnings
