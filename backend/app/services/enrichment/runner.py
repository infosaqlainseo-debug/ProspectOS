import uuid
import logging
import asyncio
from typing import List, Dict, Any

from app.db.session import async_session_maker
from app.models import Company, SEOMetric, HistoricalSnapshot, ProviderUsage, Job, JobResult, Evidence
from app.services.providers import registry

logger = logging.getLogger(__name__)

class SEOEnrichmentRunner:
    def __init__(self, job_id: str):
        self.job_id = uuid.UUID(job_id) if isinstance(job_id, str) else job_id

    async def _save_metrics(self, session, company_id: uuid.UUID, domain: str, response, provider_name: str):
        metrics_created = 0
        metrics_skipped = 0
        
        for metric in response.metrics:
            if metric.status == "NOT_AVAILABLE":
                metrics_skipped += 1
                continue
                
            # Create SEOMetric
            new_metric = SEOMetric(
                company_id=company_id,
                domain=domain,
                metric_name=metric.metric_name,
                metric_value=metric.value,
                unit=metric.unit,
                provider=provider_name,
                provider_metric_name=metric.provider_metric_name,
                provider_endpoint=metric.provider_endpoint,
                request_id=response.request_id,
                source_url=None,
                verification_status=metric.status,
                raw_reference=metric.raw_reference,
                confidence=1.0 # Deterministic API values
            )
            session.add(new_metric)
            
            # Create HistoricalSnapshot
            snapshot = HistoricalSnapshot(
                company_id=company_id,
                metric_name=f"{provider_name}_{metric.metric_name}",
                metric_value=str(metric.value),
                provider=provider_name,
                confidence=1.0
            )
            session.add(snapshot)
            
            # Create Evidence
            evidence = Evidence(
                company_id=company_id,
                field_name=metric.metric_name,
                value=str(metric.value),
                provider=provider_name,
                extraction_method="API",
                verification_status=metric.status,
                raw_reference=metric.raw_reference,
                confidence=1.0
            )
            session.add(evidence)
            
            metrics_created += 1
            
        return metrics_created, metrics_skipped

    async def _track_usage(self, session, company_id: uuid.UUID, provider_name: str, response):
        usage = ProviderUsage(
            provider=provider_name,
            job_id=self.job_id,
            company_id=company_id,
            request_count=1,
            estimated_units=response.usage_units or 1.0,
            endpoint=response.endpoint
        )
        session.add(usage)

    async def enrich_company(self, company_id: uuid.UUID) -> Dict[str, Any]:
        logger.info(f"Starting SEO Enrichment for company {company_id}")
        
        async with async_session_maker() as session:
            company = await session.get(Company, company_id)
            if not company or not company.canonical_domain:
                return {"status": "FAILED", "error": "Company not found or no canonical domain"}
                
            domain = company.canonical_domain
            
        providers = registry.get_all_providers()
        
        total_metrics_created = 0
        total_metrics_skipped = 0
        provider_errors = 0
        successful_providers = 0
        
        async with async_session_maker() as session:
            for name, provider in providers.items():
                logger.info(f"Running provider {name} on domain {domain}")
                # We can call the authority endpoint as an example, or all supported endpoints
                
                # Fetch Authority Metrics
                auth_resp = await provider.get_authority_metrics(domain)
                
                if auth_resp.error and auth_resp.error != "UNSUPPORTED":
                    provider_errors += 1
                    logger.warning(f"Provider {name} returned error: {auth_resp.error}")
                else:
                    mc, ms = await self._save_metrics(session, company_id, domain, auth_resp, name)
                    total_metrics_created += mc
                    total_metrics_skipped += ms
                    successful_providers += 1
                    
                await self._track_usage(session, company_id, name, auth_resp)
                
                # We could also fetch traffic and backlink metrics here if supported...
                traffic_resp = await provider.get_traffic_metrics(domain)
                if not traffic_resp.error or traffic_resp.error != "UNSUPPORTED":
                    if not traffic_resp.error:
                        mc, ms = await self._save_metrics(session, company_id, domain, traffic_resp, name)
                        total_metrics_created += mc
                        total_metrics_skipped += ms
                    await self._track_usage(session, company_id, name, traffic_resp)
                    
            await session.commit()
            
        status = "COMPLETED" if provider_errors == 0 else ("PARTIAL" if successful_providers > 0 else "FAILED")
        
        return {
            "status": status,
            "metrics_created": total_metrics_created,
            "metrics_skipped": total_metrics_skipped,
            "provider_errors": provider_errors
        }
