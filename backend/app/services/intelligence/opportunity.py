import uuid
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Company, SEOMetric, WebsiteScan, AIObservation, OpportunityProfile
from app.schemas.opportunity import OpportunityProfileCreate

class OpportunityEngine:
    VERSION = "1.8.0"

    def __init__(self, db: AsyncSession):
        self.db = db

    def _get_utc_now(self) -> datetime:
        return datetime.now(timezone.utc)

    async def evaluate_company(self, company_id: uuid.UUID) -> OpportunityProfileCreate:
        # Fetch evidence
        stmt_metrics = select(SEOMetric).where(SEOMetric.company_id == company_id)
        metrics = (await self.db.execute(stmt_metrics)).scalars().all()

        stmt_scan = select(WebsiteScan).where(WebsiteScan.company_id == company_id).order_by(WebsiteScan.scanned_at.desc())
        latest_scan = (await self.db.execute(stmt_scan)).scalars().first()

        stmt_obs = select(AIObservation).where(AIObservation.company_id == company_id)
        observations = (await self.db.execute(stmt_obs)).scalars().all()

        identified_problems = []
        supporting_evidence = []
        missing_information = []
        score = 0.0

        # Technical SEO Checks
        tech_issues = 0
        is_blocked = False
        if latest_scan:
            if latest_scan.http_status == 403 or latest_scan.scan_status == "ACCESS_RESTRICTED":
                is_blocked = True
                tech_issues += 1
                identified_problems.append("Automated crawler blocked by bot protection (HTTP 403)")
                supporting_evidence.append({
                    "type": "WebsiteScan",
                    "metric": "http_status",
                    "value": latest_scan.http_status,
                    "note": "Cloudflare WAF / bot challenge encountered; on-page HTML inaccessible"
                })
                missing_information.append("On-page SEO attributes (headings, title, body content) unverified due to HTTP 403 bot challenge")
                if not latest_scan.https_enabled:
                    tech_issues += 1
                    identified_problems.append("HTTPS is not enabled")
                    supporting_evidence.append({"type": "WebsiteScan", "metric": "https_enabled", "value": False})
                if latest_scan.robots_txt_status and latest_scan.robots_txt_status.upper() not in ["OK", "FOUND"]:
                    tech_issues += 1
                    identified_problems.append(f"Robots.txt issue: {latest_scan.robots_txt_status}")
                    supporting_evidence.append({"type": "WebsiteScan", "metric": "robots_txt_status", "value": latest_scan.robots_txt_status})
            else:
                if latest_scan.http_status != 200:
                    tech_issues += 1
                    identified_problems.append("Website did not return 200 OK")
                    supporting_evidence.append({"type": "WebsiteScan", "metric": "http_status", "value": latest_scan.http_status})
                if not latest_scan.https_enabled:
                    tech_issues += 1
                    identified_problems.append("HTTPS is not enabled")
                    supporting_evidence.append({"type": "WebsiteScan", "metric": "https_enabled", "value": False})
                if latest_scan.robots_txt_status != "OK":
                    tech_issues += 1
                    identified_problems.append(f"Robots.txt issue: {latest_scan.robots_txt_status}")
                    supporting_evidence.append({"type": "WebsiteScan", "metric": "robots_txt_status", "value": latest_scan.robots_txt_status})
                if not latest_scan.h1 or len(latest_scan.h1) == 0:
                    tech_issues += 1
                    identified_problems.append("Missing H1 tags")
                    supporting_evidence.append({"type": "WebsiteScan", "metric": "h1", "value": "Missing"})
        else:
            missing_information.append("Website scan data is missing")

        # Authority Checks
        dr_metric = next((m for m in metrics if m.metric_name.lower() in ['domain_rating', 'dr', 'authority_score']), None)
        traffic_metric = next((m for m in metrics if m.metric_name.lower() in ['organic_traffic', 'traffic']), None)

        low_authority = False
        if dr_metric:
            supporting_evidence.append({"type": "SEOMetric", "metric": dr_metric.metric_name, "value": dr_metric.metric_value, "provider": dr_metric.provider})
            if dr_metric.metric_value and dr_metric.metric_value < 30:
                low_authority = True
                identified_problems.append(f"Low domain authority ({dr_metric.metric_value})")
        else:
            missing_information.append("Domain Rating / Authority Score is missing")

        if traffic_metric:
            supporting_evidence.append({"type": "SEOMetric", "metric": traffic_metric.metric_name, "value": traffic_metric.metric_value, "provider": traffic_metric.provider})
            if traffic_metric.metric_value and traffic_metric.metric_value < 1000:
                identified_problems.append(f"Low organic traffic ({traffic_metric.metric_value})")
        else:
            missing_information.append("Organic traffic data is missing")

        # Content/AI Observations
        content_quality_issue = False
        for obs in observations:
            if obs.attribute_name == "content_quality" and obs.attribute_value == "POOR":
                content_quality_issue = True
                identified_problems.append("AI evaluated content quality as POOR")
                supporting_evidence.append({"type": "AIObservation", "metric": "content_quality", "value": "POOR"})

        if not observations:
            missing_information.append("AI Observations are missing")

        # Scoring Logic
        if tech_issues > 1 and not is_blocked:
            recommended_service = "Technical SEO"
            score = 80.0 + (tech_issues * 5)
        elif low_authority and not content_quality_issue:
            recommended_service = "Link building"
            score = 75.0
        elif content_quality_issue:
            recommended_service = "Content strategy"
            score = 70.0
        elif is_blocked:
            # Blocked crawl: do not artificially inflate or penalize
            recommended_service = "Website optimization"
            score = 55.0
        else:
            recommended_service = "Website optimization"
            score = 50.0

        # Cap score at 100
        score = min(score, 100.0)

        # Confidence Calculation
        total_signals = len(metrics) + (1 if (latest_scan and not is_blocked) else 0) + len(observations)
        if total_signals == 0:
            confidence = 0.0
        elif total_signals < 3:
            confidence = 0.4
        elif total_signals < 6:
            confidence = 0.7
        else:
            confidence = 0.9

        if is_blocked:
            confidence = min(confidence, 0.7)

        # Freshness
        data_freshness = "FRESH"
        now = self._get_utc_now()
        if latest_scan and (now - latest_scan.scanned_at) > timedelta(days=30):
            data_freshness = "STALE"
        if dr_metric and (now - dr_metric.retrieved_at) > timedelta(days=30):
            data_freshness = "STALE"

        next_action = "Collect missing data" if missing_information else "Manual Review"

        return OpportunityProfileCreate(
            company_id=company_id,
            recommended_service=recommended_service,
            opportunity_score=score,
            supporting_evidence=supporting_evidence,
            identified_problems=identified_problems,
            confidence_level=confidence,
            data_freshness=data_freshness,
            missing_information=missing_information,
            recommended_next_action=next_action,
            methodology_version=self.VERSION
        )

    async def save_profile(self, profile_data: OpportunityProfileCreate) -> OpportunityProfile:
        profile = OpportunityProfile(
            company_id=profile_data.company_id,
            recommended_service=profile_data.recommended_service,
            opportunity_score=profile_data.opportunity_score,
            supporting_evidence=profile_data.supporting_evidence,
            identified_problems=profile_data.identified_problems,
            confidence_level=profile_data.confidence_level,
            data_freshness=profile_data.data_freshness,
            missing_information=profile_data.missing_information,
            recommended_next_action=profile_data.recommended_next_action,
            methodology_version=profile_data.methodology_version,
            calculation_timestamp=self._get_utc_now()
        )
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile
