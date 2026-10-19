import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.core.config import settings
from app.db.session import async_session_maker
from app.models import Company, Job, Evidence, WebsiteScan
from app.models import AIExtractionRun, AIObservation, AIContradiction
from app.services.ai.providers import registry
from app.schemas.enums import VerificationStatus
from sqlalchemy import select

logger = logging.getLogger(__name__)

class AIExtractionRunner:
    def __init__(self, job_id: str, provider_name: Optional[str] = None):
        self.job_id = uuid.UUID(job_id) if isinstance(job_id, str) else job_id
        self.provider_name = provider_name

    async def _gather_evidence_text(self, session, company_id: uuid.UUID) -> str:
        # Collect recent website scan texts
        stmt = select(WebsiteScan).where(WebsiteScan.company_id == company_id).order_by(WebsiteScan.scanned_at.desc()).limit(1)
        result = await session.execute(stmt)
        scan = result.scalar_one_or_none()
        
        evidence_parts = []
        is_blocked = False
        if scan:
            if scan.http_status == 403 or (scan.scan_status == "ACCESS_RESTRICTED"):
                is_blocked = True
                evidence_parts.append(f"Notice: Direct website crawl was access-restricted (HTTP {scan.http_status} - Bot Protection / WAF). Live on-page content is unavailable.")
            else:
                if scan.title:
                    evidence_parts.append(f"Page Title: {scan.title}")
                if scan.meta_description:
                    evidence_parts.append(f"Meta Description: {scan.meta_description}")
                if scan.h1:
                    h1_str = ', '.join(scan.h1) if isinstance(scan.h1, list) else str(scan.h1)
                    evidence_parts.append(f"H1 Tags: {h1_str}")
                if scan.h2:
                    h2_str = ', '.join(scan.h2) if isinstance(scan.h2, list) else str(scan.h2)
                    evidence_parts.append(f"H2 Tags: {h2_str}")
                if scan.schema_detected:
                    evidence_parts.append(f"Schema JSON-LD: {scan.schema_detected}")
                
        company = await session.get(Company, company_id)
        if company:
            if company.company_name:
                evidence_parts.append(f"Company Name: {company.company_name}")
            if company.description:
                evidence_parts.append(f"Company Description: {company.description}")
            if company.industry:
                evidence_parts.append(f"Industry: {company.industry}")
            if company.target_market:
                evidence_parts.append(f"Target Market: {company.target_market}")

        # Fetch verified and permitted fallback evidence records
        stmt_ev = select(Evidence).where(Evidence.company_id == company_id).order_by(Evidence.created_at.desc()).limit(15)
        ev_records = (await session.execute(stmt_ev)).scalars().all()
        for ev in ev_records:
            if ev.value and (ev.confidence is None or ev.confidence >= 0.5):
                label = f"[{ev.source_type} / {ev.provider}]"
                evidence_parts.append(f"Evidence {label} {ev.field_name}: {ev.value}")

        if is_blocked:
            evidence_parts.append(
                "CRITICAL INSTRUCTION: Live on-page HTML is blocked by bot protection. "
                "Only extract verifiable company attributes from the fallback evidence above. "
                "Do NOT invent page titles, headings, or on-page SEO findings. "
                "Mark unverified on-page attributes as UNVERIFIED."
            )
            
        return "\n".join(evidence_parts)

    def _validate_attribute(self, attr_name: str, extracted_evidence) -> VerificationStatus:
        if not extracted_evidence or extracted_evidence.value is None:
            return VerificationStatus.UNVERIFIED
            
        if not extracted_evidence.evidence_text:
            return VerificationStatus.REJECTED
            
        if extracted_evidence.confidence is None or extracted_evidence.confidence < 0.50:
            return VerificationStatus.REJECTED
            
        return VerificationStatus.VERIFIED

    async def run_extraction(self, company_id: uuid.UUID) -> Dict[str, Any]:
        logger.info(f"Starting AI Extraction for company {company_id}")
        
        async with async_session_maker() as session:
            company = await session.get(Company, company_id)
            if not company:
                return {"status": "FAILED", "error": "Company not found"}
                
            evidence_text = await self._gather_evidence_text(session, company_id)
            if not evidence_text.strip():
                return {"status": "FAILED", "error": "No evidence found to run extraction"}
                
            provider_key = (self.provider_name or getattr(settings, "LLM_PROVIDER", None) or "openai").lower()
            provider = registry.get_provider(provider_key)
            if not provider:
                logger.warning(f"Provider '{provider_key}' not found in registry, falling back to openai")
                provider = registry.get_provider("openai")
                
            if not provider:
                return {"status": "FAILED", "error": f"LLM provider '{provider_key}' not available in registry"}
            
            run_record = AIExtractionRun(
                company_id=company_id,
                job_id=self.job_id,
                provider=provider.provider_name,
                model=provider.model,
                prompt_version="v1.0.0",
                schema_version="v1",
                status="RUNNING"
            )
            session.add(run_record)
            await session.commit()
            await session.refresh(run_record)
            
        # Run external LLM
        resp = await provider.extract_company_attributes(evidence_text)
        
        async with async_session_maker() as session:
            run_record = await session.get(AIExtractionRun, run_record.id)
            
            if resp.error:
                run_record.status = "FAILED"
                run_record.error_message = resp.error
                run_record.completed_at = datetime.now(timezone.utc)
                await session.commit()
                return {"status": "FAILED", "error": resp.error}
                
            run_record.status = "COMPLETED"
            run_record.total_tokens = resp.total_tokens
            run_record.estimated_cost = resp.estimated_cost
            run_record.completed_at = datetime.now(timezone.utc)
            
            observations_created = 0
            contradictions_found = 0
            
            if resp.result and resp.result.attributes:
                attributes_dict = resp.result.attributes.model_dump()
                
                for attr_name, extracted_evidence_dict in attributes_dict.items():
                    if not extracted_evidence_dict:
                        continue
                        
                    # Reconstruct pydantic object to validate easily
                    from app.schemas.ai_extraction import AIEvidence
                    extracted_evidence = AIEvidence(**extracted_evidence_dict)
                    
                    status = self._validate_attribute(attr_name, extracted_evidence)
                    
                    # Fetch existing evidence to check for contradiction
                    stmt = select(AIObservation).where(
                        AIObservation.company_id == company_id, 
                        AIObservation.attribute_name == attr_name,
                        AIObservation.verification_status == VerificationStatus.VERIFIED
                    ).order_by(AIObservation.created_at.desc()).limit(1)
                    existing_obs = (await session.execute(stmt)).scalar_one_or_none()
                    
                    if status == VerificationStatus.VERIFIED and existing_obs:
                        if existing_obs.attribute_value != str(extracted_evidence.value):
                            status = VerificationStatus.CONTRADICTED
                            contradictions_found += 1
                            
                            contradiction = AIContradiction(
                                company_id=company_id,
                                attribute_name=attr_name,
                                existing_value=existing_obs.attribute_value,
                                new_value=str(extracted_evidence.value)
                            )
                            # We will attach observation_id after creating it
                            
                    obs = AIObservation(
                        company_id=company_id,
                        extraction_run_id=run_record.id,
                        attribute_name=attr_name,
                        attribute_value=str(extracted_evidence.value) if extracted_evidence.value is not None else None,
                        evidence_text=extracted_evidence.evidence_text,
                        source_url=extracted_evidence.source_url,
                        confidence=extracted_evidence.confidence,
                        verification_status=status.value
                    )
                    session.add(obs)
                    await session.flush()
                    
                    if status == VerificationStatus.CONTRADICTED:
                        contradiction.observation_id = obs.id
                        session.add(contradiction)
                        
                    observations_created += 1
                    
            await session.commit()
            
        return {
            "status": "COMPLETED",
            "observations_created": observations_created,
            "contradictions_found": contradictions_found
        }
