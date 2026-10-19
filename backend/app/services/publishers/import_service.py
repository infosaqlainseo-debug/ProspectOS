import uuid
from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import (
    Company, Domain, PublisherRecord, PublisherObservation, 
    ImportBatch, ImportAuditRow
)
from app.schemas.publishers import PublisherMapping
import tldextract
from datetime import datetime, timezone

def get_utc_now():
    return datetime.now(timezone.utc)

def normalize_domain(url: str) -> str:
    """Normalize a URL to its canonical domain."""
    if not url or str(url).strip().lower() == "not available":
        return ""
    if not url.startswith("http"):
        url = "http://" + url
    extracted = tldextract.extract(url)
    if not extracted.suffix:
        return ""
    return f"{extracted.domain}.{extracted.suffix}".lower()

class PublisherImportService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_import_batch(self, filename: str, total_rows: int) -> ImportBatch:
        batch = ImportBatch(
            original_filename=filename,
            status="PROCESSING",
            total_rows=total_rows
        )
        self.session.add(batch)
        await self.session.commit()
        return batch

    async def process_import_batch(self, batch_id: uuid.UUID, mapping: PublisherMapping, rows: List[Dict[str, Any]], dry_run: bool = False) -> ImportBatch:
        batch = await self.session.get(ImportBatch, batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")

        valid_count = 0
        invalid_count = 0
        created_count = 0
        updated_count = 0
        skipped_count = 0
        failed_count = 0

        for index, row in enumerate(rows):
            url = row.get(mapping.url_column)
            if not url:
                invalid_count += 1
                await self._log_audit(batch_id, index, row, "FAILED", errors=["Missing URL"])
                failed_count += 1
                continue

            canonical_domain = normalize_domain(url)
            if not canonical_domain:
                invalid_count += 1
                await self._log_audit(batch_id, index, row, "FAILED", errors=["Invalid URL domain"])
                failed_count += 1
                continue

            valid_count += 1

            try:
                # 1. Match or Create Company
                stmt = select(Company).where(Company.canonical_domain == canonical_domain)
                result = await self.session.execute(stmt)
                company = result.scalars().first()

                action = "CREATED"
                if not company:
                    company = Company(
                        canonical_domain=canonical_domain,
                        website_url=url,
                        company_name=row.get(mapping.publisher_name_column) if mapping.publisher_name_column else None,
                        industry=row.get(mapping.industry_column) if mapping.industry_column else None
                    )
                    self.session.add(company)
                    await self.session.flush() # get ID
                    
                    domain_obj = Domain(
                        company_id=company.id,
                        domain=canonical_domain,
                        canonical_domain=canonical_domain,
                        status="UNVERIFIED"
                    )
                    self.session.add(domain_obj)
                    created_count += 1
                else:
                    action = "UPDATED"
                    updated_count += 1
                    # Do not overwrite existing company name blindly, maybe update industry if NULL
                    if mapping.industry_column and row.get(mapping.industry_column) and not company.industry:
                        company.industry = row.get(mapping.industry_column)

                # 2. Match or Create PublisherRecord
                stmt = select(PublisherRecord).where(PublisherRecord.company_id == company.id)
                result = await self.session.execute(stmt)
                pub_record = result.scalars().first()

                if not pub_record:
                    pub_record = PublisherRecord(
                        company_id=company.id,
                        original_submitted_url=url,
                        publisher_name=row.get(mapping.publisher_name_column) if mapping.publisher_name_column else None,
                        audience_focus=row.get(mapping.audience_column) if mapping.audience_column else None,
                        status="UNVERIFIED"
                    )
                    self.session.add(pub_record)
                    await self.session.flush()
                else:
                    # Update empty fields
                    if mapping.audience_column and row.get(mapping.audience_column) and not pub_record.audience_focus:
                        pub_record.audience_focus = row.get(mapping.audience_column)
                
                # 3. Create PublisherObservation (Historical snapshot of metrics/prices)
                def parse_float(val):
                    try:
                        return float(val) if val is not None and str(val).strip() != "" else None
                    except (ValueError, TypeError):
                        return None
                
                price = parse_float(row.get(mapping.price_column)) if mapping.price_column else None
                da = parse_float(row.get(mapping.da_column)) if mapping.da_column else None
                dr = parse_float(row.get(mapping.dr_column)) if mapping.dr_column else None
                traffic = parse_float(row.get(mapping.traffic_column)) if mapping.traffic_column else None
                
                obs = PublisherObservation(
                    publisher_id=pub_record.id,
                    price=price,
                    currency=row.get(mapping.currency_column) if mapping.currency_column else None,
                    metric_da=da,
                    metric_dr=dr,
                    metric_traffic=traffic,
                    source_name=batch.original_filename,
                    import_batch_id=batch.id,
                    verification_status="UNVERIFIED"
                )
                self.session.add(obs)
                
                await self._log_audit(batch_id, index, row, "SUCCESS", action=action, entity_id=pub_record.id)

            except Exception as e:
                # Rollback to savepoint? For now, if one fails, we just log it.
                # Since we are not doing subtransactions, we should just let the error propagate or wrap in try-except block.
                # Since we're in asyncio, we can't easily catch db errors without rolling back the whole transaction.
                # SQLAlchemy requires a rollback if an error occurs. 
                # To be robust, we'll assume no integrity errors because we check first, but if one occurs, it fails the batch.
                raise e

        # Finalize batch
        batch.valid_rows = valid_count
        batch.invalid_rows = invalid_count
        batch.created_records = created_count
        batch.updated_records = updated_count
        batch.skipped_rows = skipped_count
        batch.failed_rows = failed_count
        batch.status = "DRY_RUN" if dry_run else "COMPLETED"
        
        if dry_run:
            stats = {
                "id": batch.id,
                "original_filename": batch.original_filename,
                "status": "DRY_RUN",
                "total_rows": batch.total_rows,
                "valid_rows": batch.valid_rows,
                "invalid_rows": batch.invalid_rows,
                "created_records": batch.created_records,
                "updated_records": batch.updated_records,
                "skipped_rows": batch.skipped_rows,
                "failed_rows": batch.failed_rows,
                "created_at": batch.created_at
            }
            await self.session.rollback()
            return stats
        else:
            await self.session.commit()
            return batch

    async def _log_audit(self, batch_id: uuid.UUID, index: int, raw_data: dict, status: str, action: str = None, entity_id: uuid.UUID = None, errors: list = None):
        audit = ImportAuditRow(
            import_batch_id=batch_id,
            row_index=index,
            raw_data=raw_data,
            status=status,
            action_taken=action,
            entity_id=entity_id,
            errors=errors
        )
        self.session.add(audit)
