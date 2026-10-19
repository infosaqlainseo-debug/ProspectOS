import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_, and_

from app.models import (
    Company,
    Domain,
    WebsiteScan,
    PublisherRecord,
    PublisherObservation,
    PublisherQualityScore,
    PublisherQualityFinding,
    PublisherRefreshLog,
    CRMActivity
)
from app.schemas.publisher_quality import (
    DEFAULT_FRESHNESS_THRESHOLDS,
    PublisherQualityFindingResponse,
    PublisherQualityScoreResponse,
    PublisherQualitySummaryResponse,
    PublisherDetailedQualityResponse,
    PublisherObservationTimelineItem,
    QualitySeverityBreakdown,
    QualityIssueBreakdown
)
from app.utils.url import normalize_url, extract_canonical_domain
from app.services.providers.registry import registry

logger = logging.getLogger(__name__)

SUPPORTED_CURRENCIES = {"USD", "EUR", "GBP", "CAD", "AUD", "INR", "SGD", "JPY", "CHF"}


class PublisherQualityService:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _get_utc_now(self) -> datetime:
        return datetime.now(timezone.utc)

    # =========================================================================
    # 1. Single Publisher Audit
    # =========================================================================

    async def audit_publisher(
        self,
        publisher_id: uuid.UUID,
        freshness_thresholds: Optional[Dict[str, int]] = None
    ) -> Tuple[PublisherQualityScore, List[PublisherQualityFinding]]:
        """
        Conducts an in-depth, evidence-based quality audit for a publisher.
        Evaluates completeness, freshness, validity, duplicates, and conflicts.
        Guarantees non-fabrication and preserves historical records.
        """
        thresholds = freshness_thresholds or DEFAULT_FRESHNESS_THRESHOLDS
        price_freshness_days = thresholds.get("price_days", 30)
        metrics_freshness_days = thresholds.get("metrics_days", 60)
        site_freshness_days = thresholds.get("site_days", 14)

        now_utc = self._get_utc_now()

        publisher = await self.session.get(PublisherRecord, publisher_id)
        if not publisher:
            raise ValueError(f"Publisher {publisher_id} not found")

        company = await self.session.get(Company, publisher.company_id)
        if not company:
            raise ValueError(f"Company {publisher.company_id} associated with publisher not found")

        # Load all historical observations ordered newest first
        stmt_obs = (
            select(PublisherObservation)
            .where(PublisherObservation.publisher_id == publisher_id)
            .order_by(desc(PublisherObservation.observation_timestamp))
        )
        observations = (await self.session.execute(stmt_obs)).scalars().all()
        latest_obs = observations[0] if observations else None

        # Load latest website scan
        stmt_scan = (
            select(WebsiteScan)
            .where(WebsiteScan.company_id == company.id)
            .order_by(desc(WebsiteScan.scanned_at))
            .limit(1)
        )
        scan = (await self.session.execute(stmt_scan)).scalar_one_or_none()

        detected_findings: List[Dict[str, Any]] = []

        # -------------------------------------------------------------
        # A. URL & Domain Validation
        # -------------------------------------------------------------
        submitted_url = publisher.original_submitted_url or company.website_url
        if not submitted_url or submitted_url.strip() == "":
            detected_findings.append({
                "issue_type": "MISSING_FIELD",
                "field_name": "website_url",
                "severity": "CRITICAL",
                "title": "Missing Website URL",
                "description": "Publisher record has no recorded submission URL or company website URL.",
                "evidence": {"submitted_url": submitted_url},
                "recommended_action": "Provide the official publication website URL."
            })
        else:
            extracted_domain = extract_canonical_domain(submitted_url)
            if not extracted_domain:
                detected_findings.append({
                    "issue_type": "INVALID_DATA",
                    "field_name": "website_url",
                    "severity": "CRITICAL",
                    "title": "Invalid or Malformed Website URL",
                    "description": f"URL '{submitted_url}' cannot be parsed into a valid canonical domain.",
                    "evidence": {"submitted_url": submitted_url},
                    "recommended_action": "Update record with a valid top-level domain URL (e.g. https://example.com)."
                })
            elif company.canonical_domain and extracted_domain != company.canonical_domain:
                detected_findings.append({
                    "issue_type": "CONFLICTING_DATA",
                    "field_name": "canonical_domain",
                    "severity": "HIGH",
                    "title": "Canonical Domain Mismatch",
                    "description": f"Extracted domain '{extracted_domain}' conflicts with company canonical domain '{company.canonical_domain}'.",
                    "evidence": {
                        "extracted_domain": extracted_domain,
                        "company_canonical_domain": company.canonical_domain
                    },
                    "recommended_action": "Re-align company canonical domain with extracted publisher domain."
                })

        # -------------------------------------------------------------
        # B. Duplicate Detection
        # -------------------------------------------------------------
        has_duplicates = False
        target_domain = company.canonical_domain or (extract_canonical_domain(submitted_url) if submitted_url else None)
        if target_domain:
            stmt_dup = (
                select(PublisherRecord.id, Company.canonical_domain)
                .join(Company, Company.id == PublisherRecord.company_id)
                .where(
                    PublisherRecord.id != publisher_id,
                    or_(
                        Company.canonical_domain == target_domain,
                        PublisherRecord.original_submitted_url.ilike(f"%{target_domain}%")
                    )
                )
            )
            dups = (await self.session.execute(stmt_dup)).all()
            if dups:
                has_duplicates = True
                detected_findings.append({
                    "issue_type": "DUPLICATE_RECORD",
                    "field_name": "canonical_domain",
                    "severity": "CRITICAL",
                    "title": f"Duplicate Publisher Record Detected ({len(dups)} collisions)",
                    "description": f"Canonical domain '{target_domain}' is also claimed by other publisher record(s).",
                    "evidence": {
                        "duplicate_publisher_ids": [str(d[0]) for d in dups],
                        "canonical_domain": target_domain
                    },
                    "recommended_action": "Review duplicate inventory records and resolve duplicate publisher entry without data loss."
                })

        # -------------------------------------------------------------
        # C. Observation & Pricing Data Validation
        # -------------------------------------------------------------
        if not latest_obs:
            detected_findings.append({
                "issue_type": "MISSING_FIELD",
                "field_name": "observation",
                "severity": "CRITICAL",
                "title": "No Observations Recorded",
                "description": "Publisher has zero historical or current metric/price observations.",
                "evidence": {"observations_count": 0},
                "recommended_action": "Import inventory pricing and metrics or run provider enrichment."
            })
        else:
            # Price
            if latest_obs.price is None:
                detected_findings.append({
                    "issue_type": "MISSING_FIELD",
                    "field_name": "price",
                    "severity": "HIGH",
                    "title": "Missing Placement Price",
                    "description": "Latest publisher observation has no recorded price.",
                    "evidence": {"latest_observation_id": str(latest_obs.id)},
                    "recommended_action": "Obtain current rate card or media kit pricing from publisher."
                })
            elif latest_obs.price <= 0:
                detected_findings.append({
                    "issue_type": "INVALID_DATA",
                    "field_name": "price",
                    "severity": "CRITICAL",
                    "title": "Invalid Non-Positive Price",
                    "description": f"Recorded price {latest_obs.price} must be strictly positive.",
                    "evidence": {"price": latest_obs.price},
                    "recommended_action": "Correct pricing with verified media kit rate."
                })
            elif latest_obs.price > 50000:
                detected_findings.append({
                    "issue_type": "INVALID_DATA",
                    "field_name": "price",
                    "severity": "LOW",
                    "title": "Outlier High Price ($50,000+)",
                    "description": f"Price of ${latest_obs.price:,.2f} is exceptionally high. Confirm if this is enterprise package pricing.",
                    "evidence": {"price": latest_obs.price},
                    "recommended_action": "Verify if pricing reflects per-post rate or full sponsorship package."
                })

            # Currency
            if not latest_obs.currency or latest_obs.currency.strip() == "":
                detected_findings.append({
                    "issue_type": "MISSING_FIELD",
                    "field_name": "currency",
                    "severity": "HIGH",
                    "title": "Missing Currency Code",
                    "description": "Price is present but currency denomination is undefined.",
                    "evidence": {"price": latest_obs.price, "currency": latest_obs.currency},
                    "recommended_action": "Specify 3-letter ISO currency code (e.g. USD, EUR, GBP)."
                })
            elif latest_obs.currency.upper() not in SUPPORTED_CURRENCIES:
                detected_findings.append({
                    "issue_type": "INVALID_DATA",
                    "field_name": "currency",
                    "severity": "MEDIUM",
                    "title": f"Unrecognized Currency '{latest_obs.currency}'",
                    "description": f"Currency code '{latest_obs.currency}' is not in standard ISO supported list.",
                    "evidence": {"currency": latest_obs.currency},
                    "recommended_action": "Normalize to valid standard 3-letter currency code."
                })

            # Authority Metrics (DA/DR)
            has_da = latest_obs.metric_da is not None
            has_dr = latest_obs.metric_dr is not None
            if not has_da and not has_dr:
                detected_findings.append({
                    "issue_type": "MISSING_FIELD",
                    "field_name": "metric_da",
                    "severity": "HIGH",
                    "title": "Missing Domain Authority Metrics",
                    "description": "Neither Moz DA nor Ahrefs DR are recorded for this publisher.",
                    "evidence": {"metric_da": None, "metric_dr": None},
                    "recommended_action": "Enrich publisher domain metrics via authorized SEO provider."
                })
            else:
                if has_da and (latest_obs.metric_da < 0 or latest_obs.metric_da > 100):
                    detected_findings.append({
                        "issue_type": "INVALID_DATA",
                        "field_name": "metric_da",
                        "severity": "CRITICAL",
                        "title": "Out-of-Bounds Domain Authority",
                        "description": f"DA {latest_obs.metric_da} is outside valid 0-100 scale.",
                        "evidence": {"metric_da": latest_obs.metric_da},
                        "recommended_action": "Re-fetch or correct Domain Authority score."
                    })
                if has_dr and (latest_obs.metric_dr < 0 or latest_obs.metric_dr > 100):
                    detected_findings.append({
                        "issue_type": "INVALID_DATA",
                        "field_name": "metric_dr",
                        "severity": "CRITICAL",
                        "title": "Out-of-Bounds Domain Rating",
                        "description": f"DR {latest_obs.metric_dr} is outside valid 0-100 scale.",
                        "evidence": {"metric_dr": latest_obs.metric_dr},
                        "recommended_action": "Re-fetch or correct Domain Rating score."
                    })

            # Traffic
            if latest_obs.metric_traffic is not None and latest_obs.metric_traffic < 0:
                detected_findings.append({
                    "issue_type": "INVALID_DATA",
                    "field_name": "metric_traffic",
                    "severity": "CRITICAL",
                    "title": "Negative Organic Traffic",
                    "description": f"Organic traffic value {latest_obs.metric_traffic} cannot be negative.",
                    "evidence": {"metric_traffic": latest_obs.metric_traffic},
                    "recommended_action": "Correct traffic observation."
                })

        # Category / Audience Focus
        if not publisher.audience_focus or publisher.audience_focus.strip() == "":
            detected_findings.append({
                "issue_type": "MISSING_FIELD",
                "field_name": "audience_focus",
                "severity": "MEDIUM",
                "title": "Missing Audience / Editorial Niche",
                "description": "Publisher has no designated industry focus or topical category.",
                "evidence": {"audience_focus": publisher.audience_focus},
                "recommended_action": "Categorize publisher niche to enable accurate prospect matching."
            })

        # -------------------------------------------------------------
        # D. Conflicting Data Across Observations
        # -------------------------------------------------------------
        has_conflicts = False
        if len(observations) > 1:
            observed_prices = [o.price for o in observations if o.price is not None and o.price > 0]
            if len(set(observed_prices)) > 1:
                min_p, max_p = min(observed_prices), max(observed_prices)
                if min_p > 0 and (max_p - min_p) / min_p > 0.35: # >35% difference without documented resolution
                    has_conflicts = True
                    detected_findings.append({
                        "issue_type": "CONFLICTING_DATA",
                        "field_name": "price",
                        "severity": "HIGH",
                        "title": f"Conflicting Price Observations (${min_p:,.0f} vs ${max_p:,.0f})",
                        "description": "Multiple historical observations record significantly divergent rates across different import sources.",
                        "evidence": {
                            "distinct_prices": list(set(observed_prices)),
                            "observations_checked": len(observations)
                        },
                        "recommended_action": "Review rate discrepancy and confirm latest contractual pricing."
                    })

            observed_currencies = [o.currency.upper() for o in observations if o.currency and o.currency.strip()]
            if len(set(observed_currencies)) > 1:
                has_conflicts = True
                detected_findings.append({
                    "issue_type": "CONFLICTING_DATA",
                    "field_name": "currency",
                    "severity": "HIGH",
                    "title": f"Conflicting Currencies ({', '.join(set(observed_currencies))})",
                    "description": "Historical observations record conflicting currency symbols for this publisher.",
                    "evidence": {"distinct_currencies": list(set(observed_currencies))},
                    "recommended_action": "Standardize primary billing currency for publisher."
                })

        # -------------------------------------------------------------
        # E. Field-Level Freshness Tracking
        # -------------------------------------------------------------
        last_price_checked_at: Optional[datetime] = None
        last_metrics_checked_at: Optional[datetime] = None
        last_site_checked_at: Optional[datetime] = None

        price_freshness_status = "MISSING"
        metrics_freshness_status = "MISSING"
        site_freshness_status = "MISSING"

        # Price Freshness
        obs_with_price = next((o for o in observations if o.price is not None), None)
        if obs_with_price:
            last_price_checked_at = obs_with_price.observation_timestamp
            age_days = (now_utc - obs_with_price.observation_timestamp).days
            if age_days > price_freshness_days:
                price_freshness_status = "STALE"
                detected_findings.append({
                    "issue_type": "STALE_DATA",
                    "field_name": "price",
                    "severity": "MEDIUM",
                    "title": f"Stale Pricing Data ({age_days} days old)",
                    "description": f"Price was last verified {age_days} days ago (freshness threshold is {price_freshness_days} days).",
                    "evidence": {
                        "last_checked_at": obs_with_price.observation_timestamp.isoformat(),
                        "age_days": age_days,
                        "threshold_days": price_freshness_days
                    },
                    "recommended_action": "Re-verify pricing with publisher to confirm rate card has not changed."
                })
            else:
                price_freshness_status = "FRESH"

        # Metrics Freshness
        obs_with_metrics = next((o for o in observations if o.metric_da is not None or o.metric_dr is not None), None)
        if obs_with_metrics:
            last_metrics_checked_at = obs_with_metrics.observation_timestamp
            age_days = (now_utc - obs_with_metrics.observation_timestamp).days
            if age_days > metrics_freshness_days:
                metrics_freshness_status = "STALE"
                detected_findings.append({
                    "issue_type": "STALE_DATA",
                    "field_name": "metric_da",
                    "severity": "LOW",
                    "title": f"Stale Domain Authority Metrics ({age_days} days old)",
                    "description": f"Authority metrics were last fetched {age_days} days ago (freshness threshold is {metrics_freshness_days} days).",
                    "evidence": {
                        "last_checked_at": obs_with_metrics.observation_timestamp.isoformat(),
                        "age_days": age_days,
                        "threshold_days": metrics_freshness_days
                    },
                    "recommended_action": "Refresh domain metrics via authorized SEO API provider."
                })
            else:
                metrics_freshness_status = "FRESH"

        # Website Health Freshness
        if scan:
            last_site_checked_at = scan.scanned_at
            age_days = (now_utc - scan.scanned_at).days
            if age_days > site_freshness_days:
                site_freshness_status = "STALE"
                detected_findings.append({
                    "issue_type": "STALE_DATA",
                    "field_name": "website_url",
                    "severity": "INFO",
                    "title": f"Website Crawl Stale ({age_days} days old)",
                    "description": f"Website health was last verified {age_days} days ago.",
                    "evidence": {"last_scanned_at": scan.scanned_at.isoformat(), "age_days": age_days},
                    "recommended_action": "Run website crawl to ensure publisher domain remains active."
                })
            elif scan.http_status != 200:
                site_freshness_status = "FRESH"
                detected_findings.append({
                    "issue_type": "INVALID_DATA",
                    "field_name": "website_url",
                    "severity": "HIGH",
                    "title": f"Publisher Website Crawl Failure (HTTP {scan.http_status})",
                    "description": f"Latest crawl returned HTTP status {scan.http_status}. Site may be offline or blocking requests.",
                    "evidence": {"http_status": scan.http_status, "url": scan.url},
                    "recommended_action": "Inspect publisher URL and verify domain availability."
                })
            else:
                site_freshness_status = "FRESH"
        else:
            detected_findings.append({
                "issue_type": "MISSING_FIELD",
                "field_name": "website_url",
                "severity": "LOW",
                "title": "No Website Crawl Recorded",
                "description": "Domain has never been crawled by website scanner to verify uptime and SSL.",
                "evidence": {"has_scan": False},
                "recommended_action": "Initiate website crawl check."
            })

        # -------------------------------------------------------------
        # F. Score Computation
        # -------------------------------------------------------------
        # 1. Completeness Score (0-100)
        # Checks required fields: url, price, currency, da/dr, traffic, audience_focus
        completeness_pts = 100.0
        missing_findings = [f for f in detected_findings if f["issue_type"] == "MISSING_FIELD"]
        for f in missing_findings:
            if f["severity"] == "CRITICAL":
                completeness_pts -= 30.0
            elif f["severity"] == "HIGH":
                completeness_pts -= 15.0
            elif f["severity"] == "MEDIUM":
                completeness_pts -= 10.0
            else:
                completeness_pts -= 5.0
        completeness_score = max(0.0, completeness_pts)

        # 2. Freshness Score (0-100)
        freshness_pts = 100.0
        if price_freshness_status == "STALE":
            freshness_pts -= 35.0
        elif price_freshness_status == "MISSING":
            freshness_pts -= 25.0

        if metrics_freshness_status == "STALE":
            freshness_pts -= 25.0
        elif metrics_freshness_status == "MISSING":
            freshness_pts -= 20.0

        if site_freshness_status == "STALE":
            freshness_pts -= 15.0
        elif site_freshness_status == "MISSING":
            freshness_pts -= 10.0
        freshness_score = max(0.0, freshness_pts)

        # 3. Validity Score (0-100)
        validity_pts = 100.0
        invalid_findings = [f for f in detected_findings if f["issue_type"] == "INVALID_DATA"]
        for f in invalid_findings:
            if f["severity"] == "CRITICAL":
                validity_pts -= 35.0
            elif f["severity"] == "HIGH":
                validity_pts -= 20.0
            elif f["severity"] == "MEDIUM":
                validity_pts -= 10.0
            else:
                validity_pts -= 5.0
        validity_score = max(0.0, validity_pts)

        # 4. Consistency Score (0-100)
        consistency_pts = 100.0
        if has_duplicates:
            consistency_pts -= 40.0
        if has_conflicts:
            consistency_pts -= 30.0
        consistency_score = max(0.0, consistency_pts)

        # Overall Weighted Quality Score
        # Weights: Completeness (35%), Freshness (25%), Validity (20%), Consistency (20%)
        overall_score = (
            (completeness_score * 0.35) +
            (freshness_score * 0.25) +
            (validity_score * 0.20) +
            (consistency_score * 0.20)
        )
        overall_quality_score = round(min(max(overall_score, 0.0), 100.0), 1)

        critical_count = sum(1 for f in detected_findings if f["severity"] in ["CRITICAL", "HIGH"])
        open_issues_count = len(detected_findings)

        # -------------------------------------------------------------
        # G. Persist Findings & Score (Non-Destructive)
        # -------------------------------------------------------------
        # Query existing open findings for this publisher
        stmt_exist_findings = (
            select(PublisherQualityFinding)
            .where(
                PublisherQualityFinding.publisher_id == publisher_id,
                PublisherQualityFinding.status == "OPEN"
            )
        )
        existing_open_findings = (await self.session.execute(stmt_exist_findings)).scalars().all()

        # Build key map for existing open findings: (issue_type, field_name)
        existing_map = {(f.issue_type, f.field_name): f for f in existing_open_findings}
        detected_keys = set()

        created_or_retained_findings: List[PublisherQualityFinding] = []

        for df in detected_findings:
            key = (df["issue_type"], df["field_name"])
            detected_keys.add(key)
            if key in existing_map:
                # Update existing finding details
                ef = existing_map[key]
                ef.title = df["title"]
                ef.description = df["description"]
                ef.severity = df["severity"]
                ef.evidence = df["evidence"]
                ef.recommended_action = df["recommended_action"]
                ef.updated_at = now_utc
                created_or_retained_findings.append(ef)
            else:
                # Add new finding
                nf = PublisherQualityFinding(
                    publisher_id=publisher_id,
                    issue_type=df["issue_type"],
                    field_name=df["field_name"],
                    severity=df["severity"],
                    title=df["title"],
                    description=df["description"],
                    evidence=df["evidence"],
                    recommended_action=df["recommended_action"],
                    status="OPEN",
                    created_at=now_utc,
                    updated_at=now_utc
                )
                self.session.add(nf)
                created_or_retained_findings.append(nf)

        # Auto-resolve previously open findings that no longer appear
        for key, ef in existing_map.items():
            if key not in detected_keys:
                ef.status = "RESOLVED"
                ef.resolution_action = "REFRESHED_PROVIDER"
                ef.resolution_notes = "Automatically resolved by publisher audit: issue condition is no longer present."
                ef.resolved_by = "system_audit"
                ef.resolved_at = now_utc
                ef.updated_at = now_utc

        # Upsert QualityScore
        stmt_score = select(PublisherQualityScore).where(PublisherQualityScore.publisher_id == publisher_id)
        score_obj = (await self.session.execute(stmt_score)).scalar_one_or_none()

        if score_obj:
            score_obj.overall_quality_score = overall_quality_score
            score_obj.completeness_score = round(completeness_score, 1)
            score_obj.freshness_score = round(freshness_score, 1)
            score_obj.validity_score = round(validity_score, 1)
            score_obj.consistency_score = round(consistency_score, 1)
            score_obj.price_freshness_status = price_freshness_status
            score_obj.metrics_freshness_status = metrics_freshness_status
            score_obj.site_freshness_status = site_freshness_status
            score_obj.last_price_checked_at = last_price_checked_at
            score_obj.last_metrics_checked_at = last_metrics_checked_at
            score_obj.last_site_checked_at = last_site_checked_at
            score_obj.open_issues_count = open_issues_count
            score_obj.critical_issues_count = critical_count
            score_obj.has_duplicates = has_duplicates
            score_obj.has_conflicts = has_conflicts
            score_obj.last_audited_at = now_utc
            score_obj.updated_at = now_utc
        else:
            score_obj = PublisherQualityScore(
                publisher_id=publisher_id,
                overall_quality_score=overall_quality_score,
                completeness_score=round(completeness_score, 1),
                freshness_score=round(freshness_score, 1),
                validity_score=round(validity_score, 1),
                consistency_score=round(consistency_score, 1),
                price_freshness_status=price_freshness_status,
                metrics_freshness_status=metrics_freshness_status,
                site_freshness_status=site_freshness_status,
                last_price_checked_at=last_price_checked_at,
                last_metrics_checked_at=last_metrics_checked_at,
                last_site_checked_at=last_site_checked_at,
                open_issues_count=open_issues_count,
                critical_issues_count=critical_count,
                has_duplicates=has_duplicates,
                has_conflicts=has_conflicts,
                last_audited_at=now_utc,
                created_at=now_utc,
                updated_at=now_utc
            )
            self.session.add(score_obj)

        await self.session.commit()
        await self.session.refresh(score_obj)
        logger.info(f"Audited publisher {publisher_id}: Quality score = {score_obj.overall_quality_score}, open issues = {open_issues_count}")
        return score_obj, created_or_retained_findings

    # =========================================================================
    # 2. Batch Audit
    # =========================================================================

    async def audit_all_publishers(
        self,
        limit: int = 100,
        publisher_ids: Optional[List[uuid.UUID]] = None
    ) -> Dict[str, Any]:
        """
        Runs quality audits across a batch of publishers.
        """
        stmt = select(PublisherRecord.id)
        if publisher_ids:
            stmt = stmt.where(PublisherRecord.id.in_(publisher_ids))
        stmt = stmt.limit(limit)

        ids = (await self.session.execute(stmt)).scalars().all()
        audited_count = 0
        total_issues = 0

        for pid in ids:
            try:
                score, findings = await self.audit_publisher(pid)
                audited_count += 1
                total_issues += len(findings)
            except Exception as e:
                logger.error(f"Failed to audit publisher {pid}: {e}")

        return {
            "audited_count": audited_count,
            "total_issues_found": total_issues,
            "timestamp": self._get_utc_now().isoformat()
        }

    # =========================================================================
    # 3. Overall Summary & Metrics
    # =========================================================================

    async def get_quality_summary(self) -> PublisherQualitySummaryResponse:
        """
        Aggregates system-wide data quality statistics for publishers.
        """
        total_pubs = (await self.session.execute(select(func.count(PublisherRecord.id)))).scalar() or 0
        audited_pubs = (await self.session.execute(select(func.count(PublisherQualityScore.id)))).scalar() or 0
        avg_score = (await self.session.execute(select(func.avg(PublisherQualityScore.overall_quality_score)))).scalar() or 0.0

        pubs_with_crit = (
            await self.session.execute(
                select(func.count(PublisherQualityScore.id))
                .where(PublisherQualityScore.critical_issues_count > 0)
            )
        ).scalar() or 0

        pubs_with_stale = (
            await self.session.execute(
                select(func.count(PublisherQualityScore.id))
                .where(
                    or_(
                        PublisherQualityScore.price_freshness_status == "STALE",
                        PublisherQualityScore.metrics_freshness_status == "STALE",
                        PublisherQualityScore.site_freshness_status == "STALE"
                    )
                )
            )
        ).scalar() or 0

        pubs_with_dups = (
            await self.session.execute(
                select(func.count(PublisherQualityScore.id))
                .where(PublisherQualityScore.has_duplicates.is_(True))
            )
        ).scalar() or 0

        pubs_with_conflicts = (
            await self.session.execute(
                select(func.count(PublisherQualityScore.id))
                .where(PublisherQualityScore.has_conflicts.is_(True))
            )
        ).scalar() or 0

        total_open = (
            await self.session.execute(
                select(func.count(PublisherQualityFinding.id))
                .where(PublisherQualityFinding.status == "OPEN")
            )
        ).scalar() or 0

        # Severity Breakdown
        crit = (await self.session.execute(select(func.count(PublisherQualityFinding.id)).where(PublisherQualityFinding.status == "OPEN", PublisherQualityFinding.severity == "CRITICAL"))).scalar() or 0
        high = (await self.session.execute(select(func.count(PublisherQualityFinding.id)).where(PublisherQualityFinding.status == "OPEN", PublisherQualityFinding.severity == "HIGH"))).scalar() or 0
        med = (await self.session.execute(select(func.count(PublisherQualityFinding.id)).where(PublisherQualityFinding.status == "OPEN", PublisherQualityFinding.severity == "MEDIUM"))).scalar() or 0
        low = (await self.session.execute(select(func.count(PublisherQualityFinding.id)).where(PublisherQualityFinding.status == "OPEN", PublisherQualityFinding.severity == "LOW"))).scalar() or 0
        info = (await self.session.execute(select(func.count(PublisherQualityFinding.id)).where(PublisherQualityFinding.status == "OPEN", PublisherQualityFinding.severity == "INFO"))).scalar() or 0

        # Issue Type Breakdown
        missing = (await self.session.execute(select(func.count(PublisherQualityFinding.id)).where(PublisherQualityFinding.status == "OPEN", PublisherQualityFinding.issue_type == "MISSING_FIELD"))).scalar() or 0
        stale = (await self.session.execute(select(func.count(PublisherQualityFinding.id)).where(PublisherQualityFinding.status == "OPEN", PublisherQualityFinding.issue_type == "STALE_DATA"))).scalar() or 0
        invalid = (await self.session.execute(select(func.count(PublisherQualityFinding.id)).where(PublisherQualityFinding.status == "OPEN", PublisherQualityFinding.issue_type == "INVALID_DATA"))).scalar() or 0
        duplicate = (await self.session.execute(select(func.count(PublisherQualityFinding.id)).where(PublisherQualityFinding.status == "OPEN", PublisherQualityFinding.issue_type == "DUPLICATE_RECORD"))).scalar() or 0
        conflict = (await self.session.execute(select(func.count(PublisherQualityFinding.id)).where(PublisherQualityFinding.status == "OPEN", PublisherQualityFinding.issue_type == "CONFLICTING_DATA"))).scalar() or 0

        last_audit = (await self.session.execute(select(func.max(PublisherQualityScore.last_audited_at)))).scalar()

        return PublisherQualitySummaryResponse(
            total_publishers=total_pubs,
            audited_publishers=audited_pubs,
            average_quality_score=round(float(avg_score), 1),
            publishers_with_critical_issues=pubs_with_crit,
            publishers_with_stale_data=pubs_with_stale,
            publishers_with_duplicates=pubs_with_dups,
            publishers_with_conflicts=pubs_with_conflicts,
            total_open_findings=total_open,
            severity_breakdown=QualitySeverityBreakdown(
                critical=crit, high=high, medium=med, low=low, info=info
            ),
            issue_type_breakdown=QualityIssueBreakdown(
                missing_field=missing,
                stale_data=stale,
                invalid_data=invalid,
                duplicate_record=duplicate,
                conflicting_data=conflict
            ),
            last_audit_run_at=last_audit
        )

    # =========================================================================
    # 4. Detailed Single Publisher Dossier
    # =========================================================================

    async def get_detailed_publisher_quality(self, publisher_id: uuid.UUID) -> PublisherDetailedQualityResponse:
        """
        Returns complete quality dossier, field-level freshness, observation history,
        and open/resolved findings for a publisher.
        """
        publisher = await self.session.get(PublisherRecord, publisher_id)
        if not publisher:
            raise ValueError(f"Publisher {publisher_id} not found")

        company = await self.session.get(Company, publisher.company_id)

        # Audit if not yet audited
        stmt_score = select(PublisherQualityScore).where(PublisherQualityScore.publisher_id == publisher_id)
        score_obj = (await self.session.execute(stmt_score)).scalar_one_or_none()
        if not score_obj:
            score_obj, _ = await self.audit_publisher(publisher_id)

        # Open findings
        stmt_open = (
            select(PublisherQualityFinding)
            .where(
                PublisherQualityFinding.publisher_id == publisher_id,
                PublisherQualityFinding.status == "OPEN"
            )
            .order_by(
                desc(PublisherQualityFinding.severity == "CRITICAL"),
                desc(PublisherQualityFinding.severity == "HIGH"),
                desc(PublisherQualityFinding.created_at)
            )
        )
        open_findings = (await self.session.execute(stmt_open)).scalars().all()

        # Resolved findings
        stmt_resolved = (
            select(PublisherQualityFinding)
            .where(
                PublisherQualityFinding.publisher_id == publisher_id,
                PublisherQualityFinding.status != "OPEN"
            )
            .order_by(desc(PublisherQualityFinding.resolved_at))
            .limit(20)
        )
        resolved_findings = (await self.session.execute(stmt_resolved)).scalars().all()

        # Observation timeline (historical observations preserved!)
        stmt_obs = (
            select(PublisherObservation)
            .where(PublisherObservation.publisher_id == publisher_id)
            .order_by(desc(PublisherObservation.observation_timestamp))
        )
        obs_rows = (await self.session.execute(stmt_obs)).scalars().all()

        timeline = [
            PublisherObservationTimelineItem(
                id=o.id,
                price=o.price,
                currency=o.currency,
                pricing_model=o.pricing_model,
                metric_da=o.metric_da,
                metric_dr=o.metric_dr,
                metric_traffic=o.metric_traffic,
                observation_timestamp=o.observation_timestamp,
                source_name=o.source_name,
                verification_status=o.verification_status,
                created_at=o.created_at
            )
            for o in obs_rows
        ]

        now_utc = self._get_utc_now()
        field_freshness = {
            "price": {
                "status": score_obj.price_freshness_status,
                "last_checked_at": score_obj.last_price_checked_at.isoformat() if score_obj.last_price_checked_at else None,
                "days_since_check": (now_utc - score_obj.last_price_checked_at).days if score_obj.last_price_checked_at else None
            },
            "metrics": {
                "status": score_obj.metrics_freshness_status,
                "last_checked_at": score_obj.last_metrics_checked_at.isoformat() if score_obj.last_metrics_checked_at else None,
                "days_since_check": (now_utc - score_obj.last_metrics_checked_at).days if score_obj.last_metrics_checked_at else None
            },
            "site": {
                "status": score_obj.site_freshness_status,
                "last_checked_at": score_obj.last_site_checked_at.isoformat() if score_obj.last_site_checked_at else None,
                "days_since_check": (now_utc - score_obj.last_site_checked_at).days if score_obj.last_site_checked_at else None
            }
        }

        return PublisherDetailedQualityResponse(
            publisher_id=publisher.id,
            company_id=publisher.company_id,
            publisher_name=publisher.publisher_name or (company.company_name if company else None),
            canonical_domain=company.canonical_domain if company else None,
            original_submitted_url=publisher.original_submitted_url,
            audience_focus=publisher.audience_focus,
            status=publisher.status,
            quality_score=PublisherQualityScoreResponse.model_validate(score_obj),
            open_findings=[PublisherQualityFindingResponse.model_validate(f) for f in open_findings],
            resolved_findings=[PublisherQualityFindingResponse.model_validate(f) for f in resolved_findings],
            observations_history=timeline,
            field_freshness=field_freshness
        )

    # =========================================================================
    # 5. Safe Refresh Through Approved Sources Only
    # =========================================================================

    async def refresh_publisher(
        self,
        publisher_id: uuid.UUID,
        target_fields: List[str],
        actor: str = "user"
    ) -> Dict[str, Any]:
        """
        Refreshes domain metrics or website availability strictly through authorized sources.
        If providers are not configured, records PROVIDER_NOT_CONFIGURED and preserves existing data.
        Never fabricates metrics. Inserts a NEW observation row, preserving historical observations.
        """
        publisher = await self.session.get(PublisherRecord, publisher_id)
        if not publisher:
            raise ValueError(f"Publisher {publisher_id} not found")

        company = await self.session.get(Company, publisher.company_id)
        domain = company.canonical_domain if company else extract_canonical_domain(publisher.original_submitted_url)
        if not domain:
            raise ValueError("Cannot refresh publisher without valid domain")

        now_utc = self._get_utc_now()
        refresh_results: Dict[str, Any] = {}

        # 1. Refresh SEO Authority Metrics
        if "metrics" in target_fields:
            # Check Moz provider
            moz_provider = registry.get_provider("moz")
            if moz_provider and getattr(moz_provider, "api_key", None):
                resp = await moz_provider.get_authority_metrics(domain)
                if resp.error:
                    log = PublisherRefreshLog(
                        publisher_id=publisher_id,
                        target_field="metrics",
                        provider_attempted="Moz",
                        status="FAILED" if resp.error != "PROVIDER_NOT_CONFIGURED" else "PROVIDER_NOT_CONFIGURED",
                        error_message=resp.error,
                        initiated_by=actor,
                        created_at=now_utc
                    )
                    self.session.add(log)
                    refresh_results["metrics"] = {"status": log.status, "provider": "Moz", "error": resp.error}
                else:
                    # Successfully fetched real metric from provider!
                    da_val = next((m.value for m in resp.metrics if m.metric_name == "domain_authority"), None)
                    # Insert NEW observation to preserve history
                    new_obs = PublisherObservation(
                        publisher_id=publisher_id,
                        metric_da=da_val,
                        observation_timestamp=now_utc,
                        source_name="Moz API Refresh",
                        verification_status="VERIFIED"
                    )
                    self.session.add(new_obs)
                    log = PublisherRefreshLog(
                        publisher_id=publisher_id,
                        target_field="metrics",
                        provider_attempted="Moz",
                        status="SUCCESS",
                        details={"metric_da": da_val},
                        initiated_by=actor,
                        created_at=now_utc
                    )
                    self.session.add(log)
                    refresh_results["metrics"] = {"status": "SUCCESS", "provider": "Moz", "metric_da": da_val}
            else:
                # No provider key configured
                log = PublisherRefreshLog(
                    publisher_id=publisher_id,
                    target_field="metrics",
                    provider_attempted="SEO Provider Registry",
                    status="PROVIDER_NOT_CONFIGURED",
                    error_message="SEO provider API credentials (Moz/Ahrefs) are not configured in settings. Metrics cannot be verified.",
                    initiated_by=actor,
                    created_at=now_utc
                )
                self.session.add(log)
                refresh_results["metrics"] = {
                    "status": "PROVIDER_NOT_CONFIGURED",
                    "message": "SEO provider API credentials are not configured. Existing observations preserved without fabrication."
                }

        # 2. Refresh Website Availability
        if "site" in target_fields:
            url_to_check = publisher.original_submitted_url or (f"https://{domain}" if domain else None)
            if url_to_check:
                try:
                    import httpx
                    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                        resp = await client.get(url_to_check)
                        status_code = resp.status_code
                        # Record WebsiteScan snapshot
                        new_scan = WebsiteScan(
                            company_id=company.id,
                            url=url_to_check,
                            http_status=status_code,
                            https_enabled=str(resp.url).startswith("https"),
                            final_url=str(resp.url),
                            scan_status="COMPLETED",
                            scanned_at=now_utc
                        )
                        self.session.add(new_scan)
                        log = PublisherRefreshLog(
                            publisher_id=publisher_id,
                            target_field="site",
                            provider_attempted="WebsiteCrawler",
                            status="SUCCESS",
                            details={"http_status": status_code, "final_url": str(resp.url)},
                            initiated_by=actor,
                            created_at=now_utc
                        )
                        self.session.add(log)
                        refresh_results["site"] = {"status": "SUCCESS", "http_status": status_code}
                except Exception as e:
                    log = PublisherRefreshLog(
                        publisher_id=publisher_id,
                        target_field="site",
                        provider_attempted="WebsiteCrawler",
                        status="FAILED",
                        error_message=str(e),
                        initiated_by=actor,
                        created_at=now_utc
                    )
                    self.session.add(log)
                    refresh_results["site"] = {"status": "FAILED", "error": str(e)}

        await self.session.commit()

        # Re-run quality audit to reflect refreshed state
        score, _ = await self.audit_publisher(publisher_id)
        refresh_results["new_quality_score"] = score.overall_quality_score
        return refresh_results

    # =========================================================================
    # 6. Attributable Manual Corrections
    # =========================================================================

    async def apply_manual_correction(
        self,
        publisher_id: uuid.UUID,
        price: Optional[float] = None,
        currency: Optional[str] = None,
        metric_da: Optional[float] = None,
        metric_dr: Optional[float] = None,
        metric_traffic: Optional[float] = None,
        pricing_model: Optional[str] = None,
        notes: str = "",
        actor: str = "human_reviewer"
    ) -> PublisherObservation:
        """
        Applies a human correction to publisher rates or metrics.
        Preserves all historical observations by inserting a NEW observation record.
        Logs to CRMActivity audit timeline.
        """
        publisher = await self.session.get(PublisherRecord, publisher_id)
        if not publisher:
            raise ValueError(f"Publisher {publisher_id} not found")

        # Fetch latest observation to inherit non-overridden fields
        stmt_obs = (
            select(PublisherObservation)
            .where(PublisherObservation.publisher_id == publisher_id)
            .order_by(desc(PublisherObservation.observation_timestamp))
            .limit(1)
        )
        latest_obs = (await self.session.execute(stmt_obs)).scalar_one_or_none()

        eff_price = price if price is not None else (latest_obs.price if latest_obs else None)
        eff_currency = currency if currency is not None else (latest_obs.currency if latest_obs else "USD")
        eff_da = metric_da if metric_da is not None else (latest_obs.metric_da if latest_obs else None)
        eff_dr = metric_dr if metric_dr is not None else (latest_obs.metric_dr if latest_obs else None)
        eff_traffic = metric_traffic if metric_traffic is not None else (latest_obs.metric_traffic if latest_obs else None)
        eff_model = pricing_model if pricing_model is not None else (latest_obs.pricing_model if latest_obs else None)

        now_utc = self._get_utc_now()

        # Insert NEW observation (historical observations preserved!)
        new_obs = PublisherObservation(
            publisher_id=publisher_id,
            price=eff_price,
            currency=eff_currency.upper() if eff_currency else None,
            pricing_model=eff_model,
            metric_da=eff_da,
            metric_dr=eff_dr,
            metric_traffic=eff_traffic,
            observation_timestamp=now_utc,
            source_name=f"Manual Correction by {actor}",
            verification_status="HUMAN_VERIFIED",
            created_at=now_utc
        )
        self.session.add(new_obs)

        # Log into CRMActivity audit timeline
        act = CRMActivity(
            company_id=publisher.company_id,
            activity_type="PUBLISHER_CORRECTION",
            actor=actor,
            title=f"Publisher Data Quality Correction: {publisher.publisher_name or 'Inventory'}",
            details={
                "price": eff_price,
                "currency": eff_currency,
                "metric_da": eff_da,
                "metric_dr": eff_dr,
                "notes": notes,
                "timestamp": now_utc.isoformat()
            },
            created_at=now_utc
        )
        self.session.add(act)

        await self.session.commit()
        await self.session.refresh(new_obs)

        # Re-audit to update quality score and clear resolved findings
        await self.audit_publisher(publisher_id)
        logger.info(f"Recorded attributable manual correction for publisher {publisher_id} by {actor}")
        return new_obs

    # =========================================================================
    # 7. Safe Finding Resolution Workflow
    # =========================================================================

    async def resolve_finding(
        self,
        finding_id: uuid.UUID,
        action: str,
        notes: Optional[str] = None,
        actor: str = "human_reviewer"
    ) -> PublisherQualityFinding:
        """
        Resolves or dismisses a quality finding with documented human justification.
        Does not automatically delete records to prevent data loss.
        """
        finding = await self.session.get(PublisherQualityFinding, finding_id)
        if not finding:
            raise ValueError(f"Finding {finding_id} not found")

        now_utc = self._get_utc_now()
        target_status = "DISMISSED" if "DISMISSED" in action else "RESOLVED"

        finding.status = target_status
        finding.resolution_action = action
        finding.resolution_notes = notes
        finding.resolved_by = actor
        finding.resolved_at = now_utc
        finding.updated_at = now_utc

        publisher = await self.session.get(PublisherRecord, finding.publisher_id)
        if publisher:
            act = CRMActivity(
                company_id=publisher.company_id,
                activity_type="QUALITY_FINDING_RESOLVED",
                actor=actor,
                title=f"Publisher Quality Finding Resolved: {finding.title} ({action})",
                details={
                    "finding_id": str(finding.id),
                    "issue_type": finding.issue_type,
                    "field_name": finding.field_name,
                    "action": action,
                    "notes": notes,
                    "timestamp": now_utc.isoformat()
                },
                created_at=now_utc
            )
            self.session.add(act)

        await self.session.commit()
        await self.session.refresh(finding)

        # Re-audit publisher to reflect updated finding count
        await self.audit_publisher(finding.publisher_id)
        return finding
