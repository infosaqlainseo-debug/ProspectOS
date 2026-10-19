import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.discovery import DiscoveryRequest
from app.services.discovery.base import DiscoveryProvider
from app.utils.url import normalize_url, extract_canonical_domain
from app.utils.http import validate_website
from app.models import Job, JobResult, Company, Domain, Source, Discovery, Evidence

logger = logging.getLogger(__name__)

async def run_discovery_pipeline(job_id: uuid.UUID, request: DiscoveryRequest, provider: DiscoveryProvider, session: AsyncSession):
    # 1. Load Job
    job = await session.get(Job, job_id)
    if not job:
        logger.error(f"Job {job_id} not found.")
        return

    job.status = "RUNNING"
    job.started_at = datetime.now(timezone.utc)
    job.discovered_count = 0
    job.validated_count = 0
    job.stored_count = 0
    job.duplicate_count = 0
    job.failed_count = 0
    await session.commit()
    
    try:
        async for batch in provider.discover(request):
            for result in batch:
                job.discovered_count += 1
                
                # 2. Parse & Normalize
                normalized_url = normalize_url(result.website_url)
                canonical_domain = extract_canonical_domain(normalized_url or result.website_url)
                
                if not canonical_domain:
                    job.failed_count += 1
                    # Log JobResult for failure
                    session.add(JobResult(
                        job_id=job.id,
                        status="FAILED",
                        stage="PARSE",
                        error_message="Could not extract canonical domain"
                    ))
                    continue
                    
                result.canonical_domain = canonical_domain

                # 3. Deduplicate
                domain_query = await session.execute(
                    select(Domain).where(Domain.canonical_domain == canonical_domain)
                )
                existing_domain = domain_query.scalars().first()
                
                if existing_domain:
                    job.duplicate_count += 1
                    company_id = existing_domain.company_id
                    
                    # Update Company last_seen_at
                    company = await session.get(Company, company_id)
                    if company:
                        company.last_seen_at = datetime.now(timezone.utc)
                        
                    # Find or Create Source
                    source_query = await session.execute(
                        select(Source).where(Source.name == result.source_name)
                    )
                    source = source_query.scalars().first()
                    if not source:
                        source = Source(
                            name=result.source_name,
                            source_type="public_directory"
                        )
                        session.add(source)
                        await session.flush()
                        
                    discovery = Discovery(
                        company_id=company_id,
                        source_id=source.id,
                        discovery_method=result.discovery_method,
                        source_url=result.source_url,
                        query=request.query,
                        job_id=job.id
                    )
                    session.add(discovery)
                    await session.commit()
                    continue

                # 4. Validate
                is_valid = await validate_website(normalized_url)
                if not is_valid:
                    job.failed_count += 1
                    session.add(JobResult(
                        job_id=job.id,
                        status="FAILED",
                        stage="VALIDATE",
                        error_message="Website failed HTTP validation"
                    ))
                    await session.commit()
                    continue
                    
                job.validated_count += 1
                
                # 5. Persist
                now = datetime.now(timezone.utc)
                company = Company(
                    company_name=result.company_name,
                    industry=result.industry,
                    first_discovered_at=now,
                    last_seen_at=now,
                    canonical_domain=canonical_domain
                )
                session.add(company)
                await session.flush()
                
                domain = Domain(
                    company_id=company.id,
                    domain=normalized_url or canonical_domain,
                    canonical_domain=canonical_domain,
                    status="ACTIVE"
                )
                session.add(domain)
                
                source_query = await session.execute(
                    select(Source).where(Source.name == result.source_name)
                )
                source = source_query.scalars().first()
                if not source:
                    source = Source(
                        name=result.source_name,
                        source_type="public_directory"
                    )
                    session.add(source)
                    await session.flush()
                
                discovery = Discovery(
                    company_id=company.id,
                    source_id=source.id,
                    discovery_method=result.discovery_method,
                    source_url=result.source_url,
                    query=request.query,
                    job_id=job.id
                )
                session.add(discovery)
                
                evidence = Evidence(
                    company_id=company.id,
                    field_name="company_existence",
                    value=result.company_name,
                    source_url=result.source_url,
                    source_type="public_directory",
                    provider=provider.source_name,
                    extraction_method=result.discovery_method,
                    confidence=result.confidence,
                    verification_status="UNVERIFIED"
                )
                session.add(evidence)
                
                session.add(JobResult(
                    job_id=job.id,
                    company_id=company.id,
                    status="COMPLETED",
                    stage="PERSIST"
                ))
                
                job.stored_count += 1
                await session.commit()

                # 6. Stop if target reached
                if job.stored_count >= request.target_count:
                    break
            
            if job.stored_count >= request.target_count:
                break
                
        # 7. Report / Finalize Job
        if job.stored_count >= request.target_count:
            job.status = "COMPLETED"
        elif job.stored_count > 0:
            job.status = "PARTIAL"
        else:
            job.status = "FAILED"
            job.error_message = "No valid companies found."
            
        job.completed_at = datetime.now(timezone.utc)
        await session.commit()

    except Exception as e:
        logger.exception(f"Pipeline error for job {job_id}: {e}")
        job.status = "FAILED"
        job.error_message = str(e)
        job.completed_at = datetime.now(timezone.utc)
        await session.commit()
