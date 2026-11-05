import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.models import Company, CRMActivity
from app.models.crm import CRMUserPreference, CRMFeedbackLog

logger = logging.getLogger(__name__)


DEFAULT_WEIGHTS = {
    "contact_reachability": 1.0,
    "profile_completeness": 1.0,
    "website_viability": 1.0,
    "seo_opportunity": 1.0,
    "preferred_industry_boost": 1.2,
    "preferred_country_boost": 1.15
}


class AdaptiveLearningService:
    """
    Adaptive AI Learning Engine that analyzes user qualification patterns,
    rejections, and stage movements to personalize lead scoring and recommendations.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_user_preferences(self, user_id: str = "default_user") -> CRMUserPreference:
        stmt = select(CRMUserPreference).where(CRMUserPreference.user_id == user_id)
        pref = (await self.session.execute(stmt)).scalars().first()
        if not pref:
            pref = CRMUserPreference(
                user_id=user_id,
                preferred_industries=[],
                preferred_countries=[],
                min_lead_score=50.0,
                scoring_weights=DEFAULT_WEIGHTS.copy(),
                target_market_rules={"target_company_sizes": ["11-50", "51-200"]}
            )
            self.session.add(pref)
            await self.session.commit()
            await self.session.refresh(pref)
        return pref

    async def log_user_feedback(
        self,
        company_id: uuid.UUID,
        action_taken: str,
        previous_stage: Optional[str] = None,
        new_stage: Optional[str] = None,
        previous_score: Optional[float] = None,
        new_score: Optional[float] = None,
        feedback_reason: Optional[str] = None,
        actor: str = "human_reviewer"
    ) -> CRMFeedbackLog:
        """Records a user feedback event and incrementally updates adaptive weights."""
        log = CRMFeedbackLog(
            company_id=company_id,
            action_taken=action_taken,
            previous_stage=previous_stage,
            new_stage=new_stage,
            previous_score=previous_score,
            new_score=new_score,
            feedback_reason=feedback_reason,
            actor=actor
        )
        self.session.add(log)

        # Trigger adaptive preference update
        await self._adapt_preferences_from_feedback(company_id, action_taken, feedback_reason)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def _adapt_preferences_from_feedback(
        self,
        company_id: uuid.UUID,
        action_taken: str,
        feedback_reason: Optional[str] = None
    ) -> None:
        company = await self.session.get(Company, company_id)
        if not company:
            return

        pref = await self.get_or_create_user_preferences("default_user")
        industries = list(pref.preferred_industries or [])
        countries = list(pref.preferred_countries or [])
        weights = dict(pref.scoring_weights or DEFAULT_WEIGHTS)

        if action_taken in ["QUALIFIED", "STAGE_CHANGE_WON", "MEETING_SCHEDULED"]:
            # Reinforce industry preference
            if company.industry and company.industry not in industries:
                industries.append(company.industry)
            # Reinforce country preference
            if company.country and company.country not in countries:
                countries.append(company.country)
            # Increase weight for reachability if company has email
            if company.public_email:
                weights["contact_reachability"] = round(min(2.0, weights.get("contact_reachability", 1.0) + 0.05), 2)

        elif action_taken in ["REJECTED", "NOT_A_FIT", "LOST"]:
            # If rejected because of missing contact info
            if not company.public_email and not company.phone_number:
                weights["contact_reachability"] = round(min(2.5, weights.get("contact_reachability", 1.0) + 0.1), 2)
            # If rejected because low quality
            if (company.lead_score or 0) < 50:
                pref.min_lead_score = min(70.0, pref.min_lead_score + 1.0)

        pref.preferred_industries = industries[:10]  # keep top 10
        pref.preferred_countries = countries[:10]
        pref.scoring_weights = weights
        pref.updated_at = datetime.now(timezone.utc)
        self.session.add(pref)

    async def get_adaptive_insights(self, user_id: str = "default_user") -> Dict[str, Any]:
        """Returns explainable insights into what the AI has learned from reviewer feedback."""
        pref = await self.get_or_create_user_preferences(user_id)

        # Feedback stats
        total_feedback = (await self.session.execute(select(func.count(CRMFeedbackLog.id)))).scalar() or 0
        qualified_count = (await self.session.execute(
            select(func.count(CRMFeedbackLog.id)).where(CRMFeedbackLog.action_taken.in_(["QUALIFIED", "STAGE_CHANGE_WON"]))
        )).scalar() or 0
        rejected_count = (await self.session.execute(
            select(func.count(CRMFeedbackLog.id)).where(CRMFeedbackLog.action_taken.in_(["REJECTED", "NOT_A_FIT"]))
        )).scalar() or 0

        # Recent logs
        recent_stmt = select(CRMFeedbackLog).order_by(desc(CRMFeedbackLog.created_at)).limit(10)
        recent_logs = (await self.session.execute(recent_stmt)).scalars().all()

        learned_patterns = []
        if pref.preferred_industries:
            learned_patterns.append({
                "type": "INDUSTRY_PREFERENCE",
                "summary": f"Prioritizing leads in: {', '.join(pref.preferred_industries[:4])}",
                "confidence": 0.88
            })
        if pref.preferred_countries:
            learned_patterns.append({
                "type": "GEO_PREFERENCE",
                "summary": f"Targeting companies located in: {', '.join(pref.preferred_countries[:4])}",
                "confidence": 0.92
            })
        if (pref.scoring_weights or {}).get("contact_reachability", 1.0) > 1.2:
            learned_patterns.append({
                "type": "CONTACT_PENALTY",
                "summary": "Weight increased for verified business email and direct reachability due to reviewer rejection patterns.",
                "confidence": 0.85
            })

        return {
            "user_id": pref.user_id,
            "total_feedback_events": total_feedback,
            "qualified_count": qualified_count,
            "rejected_count": rejected_count,
            "min_lead_score": pref.min_lead_score,
            "scoring_weights": pref.scoring_weights,
            "preferred_industries": pref.preferred_industries,
            "preferred_countries": pref.preferred_countries,
            "learned_patterns": learned_patterns,
            "recent_feedback": [
                {
                    "id": str(log.id),
                    "company_id": str(log.company_id),
                    "action_taken": log.action_taken,
                    "previous_stage": log.previous_stage,
                    "new_stage": log.new_stage,
                    "feedback_reason": log.feedback_reason,
                    "created_at": log.created_at.isoformat()
                }
                for log in recent_logs
            ]
        }

    async def reset_preferences(self, user_id: str = "default_user") -> CRMUserPreference:
        pref = await self.get_or_create_user_preferences(user_id)
        pref.preferred_industries = []
        pref.preferred_countries = []
        pref.min_lead_score = 50.0
        pref.scoring_weights = DEFAULT_WEIGHTS.copy()
        pref.target_market_rules = {}
        pref.updated_at = datetime.now(timezone.utc)
        self.session.add(pref)
        await self.session.commit()
        await self.session.refresh(pref)
        return pref

