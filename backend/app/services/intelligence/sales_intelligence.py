import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_

from app.models import (
    Company,
    WebsiteScan,
    SEOMetric,
    AIObservation,
    PublisherRecord,
    PublisherObservation,
    SalesIntelligenceScore,
    SalesOpportunity,
    SalesBrief,
    CRMActivity,
    CRMDeal
)
from app.schemas.sales_intelligence import (
    VALID_OPPORTUNITY_CATEGORIES,
    VALID_SEVERITIES,
    VALID_GROKXSEO_SERVICES,
    VALID_REVIEW_STATUSES,
    DEFAULT_SCORING_WEIGHTS,
    OpportunityItemResponse,
    SalesIntelligenceScoreResponse,
    SalesBriefResponse,
    PrioritizedProspectItem,
    ProspectComparisonDetail,
    ProspectComparisonResponse
)

logger = logging.getLogger(__name__)

SCORING_VERSION = "v3.0.0"


class SalesIntelligenceService:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _get_utc_now(self) -> datetime:
        return datetime.now(timezone.utc)

    # =========================================================================
    # 1. Opportunity Detection & Classification
    # =========================================================================

    async def detect_opportunities(self, company_id: uuid.UUID) -> List[SalesOpportunity]:
        """
        Detects granular SEO, technical, content, backlink, and publisher opportunities
        grounded in actual database records (WebsiteScan, SEOMetric, AIObservation, PublisherRecord).
        Zero invented or fabricated metrics.
        """
        company = await self.session.get(Company, company_id)
        if not company:
            raise ValueError(f"Company {company_id} not found")

        # 1. Fetch latest WebsiteScan
        stmt_scan = (
            select(WebsiteScan)
            .where(WebsiteScan.company_id == company_id)
            .order_by(desc(WebsiteScan.scanned_at))
            .limit(1)
        )
        scan = (await self.session.execute(stmt_scan)).scalar_one_or_none()

        # 2. Fetch SEO Metrics
        stmt_metrics = (
            select(SEOMetric)
            .where(SEOMetric.company_id == company_id)
        )
        metrics = (await self.session.execute(stmt_metrics)).scalars().all()

        # 3. Fetch AI Observations
        stmt_obs = (
            select(AIObservation)
            .where(AIObservation.company_id == company_id)
        )
        observations = (await self.session.execute(stmt_obs)).scalars().all()

        # 4. Fetch Publisher Inventory Alignment
        industry_query = company.industry or ""
        stmt_pub = (
            select(PublisherRecord, PublisherObservation, Company.canonical_domain)
            .join(PublisherObservation, PublisherObservation.publisher_id == PublisherRecord.id)
            .join(Company, Company.id == PublisherRecord.company_id)
            .order_by(desc(PublisherObservation.observation_timestamp))
            .limit(5)
        )
        if industry_query:
            stmt_pub = stmt_pub.where(PublisherRecord.audience_focus.ilike(f"%{industry_query}%"))
        pub_matches = (await self.session.execute(stmt_pub)).all()

        detected_opps: List[SalesOpportunity] = []
        now_utc = self._get_utc_now()

        # -------------------------------------------------------------
        # A. Technical SEO & Indexability Checks
        # -------------------------------------------------------------
        if scan:
            is_blocked = (scan.http_status == 403 or scan.scan_status == "ACCESS_RESTRICTED")

            # 1. HTTP Status & Crawl Access Check
            if is_blocked:
                tech_signals = scan.technology_signals or {}
                reason = tech_signals.get("failure_reason") or "BOT_PROTECTION_CHALLENGE"
                detected_opps.append(
                    SalesOpportunity(
                        company_id=company_id,
                        category="INDEXABILITY_CRAWLABILITY",
                        title=f"Automated Crawler Blocked by Bot Protection (HTTP {scan.http_status})",
                        description=f"Direct HTTP crawl encountered a bot protection challenge (HTTP {scan.http_status} - {reason}). Automated crawler access was restricted.",
                        severity="MEDIUM",
                        impact_rationale="Bot protection challenges automated crawlers. Search engine bots (e.g. Googlebot) may have legitimate access via allowlists, but automated on-page auditing is restricted. On-page SEO signals remain unverified.",
                        confidence=0.9,
                        recommended_service="TECHNICAL_SEO",
                        supporting_evidence=[{
                            "source_type": "WebsiteScan",
                            "field_name": "http_status",
                            "value": scan.http_status,
                            "failure_reason": reason,
                            "scanned_at": scan.scanned_at.isoformat() if scan.scanned_at else None
                        }],
                        status="ACTIVE",
                        detection_rule="CRAWL_BOT_PROTECTION_CHALLENGE",
                        detection_timestamp=now_utc
                    )
                )
            elif scan.http_status != 200:
                detected_opps.append(
                    SalesOpportunity(
                        company_id=company_id,
                        category="TECHNICAL_SEO",
                        title=f"Non-200 Server Response (HTTP {scan.http_status})",
                        description=f"Target URL returned HTTP status {scan.http_status} during scan, preventing search engine bots from reliably indexing content.",
                        severity="CRITICAL",
                        impact_rationale="Unresolved non-200 status causes crawl abandonment and drops organic search indexation completely.",
                        confidence=1.0,
                        recommended_service="TECHNICAL_SEO",
                        supporting_evidence=[{
                            "source_type": "WebsiteScan",
                            "field_name": "http_status",
                            "value": scan.http_status,
                            "scanned_at": scan.scanned_at.isoformat() if scan.scanned_at else None
                        }],
                        status="ACTIVE",
                        detection_rule="TECH_HTTP_STATUS_NON_200",
                        detection_timestamp=now_utc
                    )
                )

            # 2. HTTPS Security Protocol
            if not scan.https_enabled:
                detected_opps.append(
                    SalesOpportunity(
                        company_id=company_id,
                        category="TECHNICAL_SEO",
                        title="Unsecured HTTP Connection (Missing SSL/HTTPS)",
                        description="Website communicates over unencrypted HTTP, causing browser security warnings and negative Google ranking signals.",
                        severity="HIGH",
                        impact_rationale="HTTPS is a confirmed Google core ranking signal and protects user trust and conversion rates.",
                        confidence=1.0,
                        recommended_service="TECHNICAL_SEO",
                        supporting_evidence=[{
                            "source_type": "WebsiteScan",
                            "field_name": "https_enabled",
                            "value": False
                        }],
                        status="ACTIVE",
                        detection_rule="TECH_HTTPS_ABSENT",
                        detection_timestamp=now_utc
                    )
                )

            # 3. Robots.txt Indexation Directives
            if scan.robots_txt_status and scan.robots_txt_status.upper() not in ["OK", "FOUND"]:
                detected_opps.append(
                    SalesOpportunity(
                        company_id=company_id,
                        category="INDEXABILITY_CRAWLABILITY",
                        title=f"Robots.txt Crawl Directive Problem ({scan.robots_txt_status})",
                        description=f"Robots.txt status is '{scan.robots_txt_status}'. Improper directives risk blocking legitimate search spiders from crawling priority pages.",
                        severity="HIGH",
                        impact_rationale="Malformatted or restrictive robots.txt directives prevent organic crawlers from accessing key site sections.",
                        confidence=0.9,
                        recommended_service="TECHNICAL_SEO",
                        supporting_evidence=[{
                            "source_type": "WebsiteScan",
                            "field_name": "robots_txt_status",
                            "value": scan.robots_txt_status
                        }],
                        status="ACTIVE",
                        detection_rule="CRAWL_ROBOTS_TXT_ISSUE",
                        detection_timestamp=now_utc
                    )
                )

            # On-page content checks: ONLY evaluate when scan was not blocked and has accessible page content
            if not is_blocked and (scan.http_status == 200 or scan.title is not None):
                # 4. Page Title Metadata
                if not scan.title or scan.title.strip() == "":
                    detected_opps.append(
                        SalesOpportunity(
                            company_id=company_id,
                            category="PAGE_METADATA",
                            title="Missing Primary HTML Title Tag",
                            description="Homepage lacks a valid HTML <title> element, forcing Google to generate automated snippet titles in SERPs.",
                            severity="HIGH",
                            impact_rationale="Title tags are the single most influential on-page keyword signal for SERP CTR and ranking relevance.",
                            confidence=1.0,
                            recommended_service="CONTENT_STRATEGY",
                            supporting_evidence=[{
                                "source_type": "WebsiteScan",
                                "field_name": "title",
                                "value": None
                            }],
                            status="ACTIVE",
                            detection_rule="META_MISSING_TITLE",
                            detection_timestamp=now_utc
                        )
                    )
                elif len(scan.title) < 25:
                    detected_opps.append(
                        SalesOpportunity(
                            company_id=company_id,
                            category="PAGE_METADATA",
                            title=f"Under-Optimized Short Title Tag ({len(scan.title)} chars)",
                            description=f"Current title ('{scan.title}') is too short to capture keyword intent and secondary brand modifiers.",
                            severity="MEDIUM",
                            impact_rationale="Titles under 30 characters underutilize available SERP pixel width and forfeit valuable keyword real estate.",
                            confidence=0.95,
                            recommended_service="CONTENT_STRATEGY",
                            supporting_evidence=[{
                                "source_type": "WebsiteScan",
                                "field_name": "title",
                                "value": scan.title,
                                "length": len(scan.title)
                            }],
                            status="ACTIVE",
                            detection_rule="META_SHORT_TITLE",
                            detection_timestamp=now_utc
                        )
                    )

                # 5. Meta Description
                if not scan.meta_description or scan.meta_description.strip() == "":
                    detected_opps.append(
                        SalesOpportunity(
                            company_id=company_id,
                            category="PAGE_METADATA",
                            title="Missing Meta Description Tag",
                            description="No meta description found. Search engines will pull arbitrary text snippets from page body for SERP display.",
                            severity="MEDIUM",
                            impact_rationale="Compelling meta descriptions increase SERP click-through rates (CTR) by up to 25%.",
                            confidence=1.0,
                            recommended_service="CONTENT_STRATEGY",
                            supporting_evidence=[{
                                "source_type": "WebsiteScan",
                                "field_name": "meta_description",
                                "value": None
                            }],
                            status="ACTIVE",
                            detection_rule="META_MISSING_DESCRIPTION",
                            detection_timestamp=now_utc
                        )
                    )

                # 6. H1 Heading Tag
                if not scan.h1 or len(scan.h1) == 0:
                    detected_opps.append(
                        SalesOpportunity(
                            company_id=company_id,
                            category="PAGE_METADATA",
                            title="Missing Primary H1 Heading Tag",
                            description="Homepage contains no H1 tag, leaving the page's topical hierarchy ambiguous to search crawlers.",
                            severity="MEDIUM",
                            impact_rationale="H1 headings structure page content hierarchy and establish primary topical relevance.",
                            confidence=1.0,
                            recommended_service="CONTENT_ARCHITECTURE",
                            supporting_evidence=[{
                                "source_type": "WebsiteScan",
                                "field_name": "h1",
                                "value": []
                            }],
                            status="ACTIVE",
                            detection_rule="META_MISSING_H1",
                            detection_timestamp=now_utc
                        )
                    )

                # 7. Word Count & Content Thinness
                tech_signals = scan.technology_signals or {}
                word_count = tech_signals.get("word_count") or getattr(scan, "word_count", None) or 0
                if word_count > 0 and word_count < 250:
                    detected_opps.append(
                        SalesOpportunity(
                            company_id=company_id,
                            category="CONTENT_COVERAGE",
                            title=f"Thin On-Page Content ({word_count} words)",
                            description=f"Homepage has only {word_count} words of text content, signaling thin content risks to search engine algorithms.",
                            severity="HIGH",
                            impact_rationale="Pages with fewer than 300 words struggle to rank for competitive commercial and informational queries.",
                            confidence=0.9,
                            recommended_service="CONTENT_STRATEGY",
                            supporting_evidence=[{
                                "source_type": "WebsiteScan",
                                "field_name": "word_count",
                                "value": word_count
                            }],
                            status="ACTIVE",
                            detection_rule="CONTENT_LOW_WORD_COUNT",
                            detection_timestamp=now_utc
                        )
                    )

        # -------------------------------------------------------------
        # B. Backlink Authority & Search Performance Deficits
        # -------------------------------------------------------------
        dr_metric = next((m for m in metrics if m.metric_name.lower() in ["domain_rating", "dr", "authority_score"]), None)
        traffic_metric = next((m for m in metrics if m.metric_name.lower() in ["organic_traffic", "traffic"]), None)
        ref_domains_metric = next((m for m in metrics if m.metric_name.lower() in ["referring_domains", "ref_domains"]), None)

        if dr_metric and dr_metric.metric_value is not None:
            if dr_metric.metric_value < 25.0:
                detected_opps.append(
                    SalesOpportunity(
                        company_id=company_id,
                        category="BACKLINK_AUTHORITY",
                        title=f"Low Domain Authority Deficit ({dr_metric.metric_name.upper()} {dr_metric.metric_value:.1f})",
                        description=f"Observed domain authority of {dr_metric.metric_value:.1f} places this domain at a backlink disadvantage relative to industry leaders.",
                        severity="HIGH",
                        impact_rationale="Competitive keyword rankings require authoritative third-party backlink endorsements from reputable publishers.",
                        confidence=0.95,
                        recommended_service="LINK_BUILDING",
                        supporting_evidence=[{
                            "source_type": "SEOMetric",
                            "metric_name": dr_metric.metric_name,
                            "value": dr_metric.metric_value,
                            "provider": dr_metric.provider
                        }],
                        status="ACTIVE",
                        detection_rule="AUTH_LOW_DOMAIN_RATING",
                        detection_timestamp=now_utc
                    )
                )

        if ref_domains_metric and ref_domains_metric.metric_value is not None:
            if ref_domains_metric.metric_value < 20.0:
                detected_opps.append(
                    SalesOpportunity(
                        company_id=company_id,
                        category="BACKLINK_AUTHORITY",
                        title=f"Sparse Referring Domain Profile ({int(ref_domains_metric.metric_value)} referring domains)",
                        description=f"Domain has only {int(ref_domains_metric.metric_value)} referring domains, indicating an underdeveloped backlink footprint.",
                        severity="HIGH",
                        impact_rationale="Diversity in referring domains is a foundational ranking signal for long-term algorithmic stability.",
                        confidence=0.9,
                        recommended_service="LINK_BUILDING",
                        supporting_evidence=[{
                            "source_type": "SEOMetric",
                            "metric_name": ref_domains_metric.metric_name,
                            "value": ref_domains_metric.metric_value,
                            "provider": ref_domains_metric.provider
                        }],
                        status="ACTIVE",
                        detection_rule="AUTH_LOW_REFERRING_DOMAINS",
                        detection_timestamp=now_utc
                    )
                )

        if traffic_metric and traffic_metric.metric_value is not None:
            if traffic_metric.metric_value < 500.0:
                detected_opps.append(
                    SalesOpportunity(
                        company_id=company_id,
                        category="CONTENT_COVERAGE",
                        title=f"Low Organic Traffic Foothold (~{int(traffic_metric.metric_value)} visits/mo)",
                        description=f"Estimated organic monthly traffic is {int(traffic_metric.metric_value)}, indicating untapped search demand in this market.",
                        severity="MEDIUM",
                        impact_rationale="Comprehensive keyword mapping and content clusters can capture high-intent commercial search volume.",
                        confidence=0.85,
                        recommended_service="SEO_STRATEGY",
                        supporting_evidence=[{
                            "source_type": "SEOMetric",
                            "metric_name": traffic_metric.metric_name,
                            "value": traffic_metric.metric_value,
                            "provider": traffic_metric.provider
                        }],
                        status="ACTIVE",
                        detection_rule="SEARCH_LOW_ORGANIC_TRAFFIC",
                        detection_timestamp=now_utc
                    )
                )

        # -------------------------------------------------------------
        # C. AI Observations & Qualitative Content Flags
        # -------------------------------------------------------------
        for obs in observations:
            obs_conf = getattr(obs, "confidence", None) or getattr(obs, "confidence_score", None)
            if obs.attribute_name == "content_quality" and obs.attribute_value == "POOR":
                detected_opps.append(
                    SalesOpportunity(
                        company_id=company_id,
                        category="CONTENT_COVERAGE",
                        title="AI-Evaluated Content Quality Deficit",
                        description="Content extraction identified unstructured or low-relevance copy across primary landing pages.",
                        severity="HIGH",
                        impact_rationale="Helpful Content System penalizes low-value, unoriginal copy that fails to directly answer user intent.",
                        confidence=obs_conf or 0.8,
                        recommended_service="CONTENT_STRATEGY",
                        supporting_evidence=[{
                            "source_type": "AIObservation",
                            "attribute_name": obs.attribute_name,
                            "value": obs.attribute_value,
                            "confidence": obs_conf
                        }],
                        status="ACTIVE",
                        detection_rule="AI_CONTENT_QUALITY_POOR",
                        detection_timestamp=now_utc
                    )
                )
            elif obs.attribute_name == "value_proposition" and obs.attribute_value in ["UNCLEAR", "MISSING"]:
                detected_opps.append(
                    SalesOpportunity(
                        company_id=company_id,
                        category="CONTENT_ARCHITECTURE",
                        title="Unclear Brand Value Proposition",
                        description="Above-the-fold content fails to communicate core service benefits, hurting conversion and engagement dwell time.",
                        severity="MEDIUM",
                        impact_rationale="Clear value propositions improve bounce rate and visitor engagement signals, assisting organic conversion.",
                        confidence=obs_conf or 0.75,
                        recommended_service="CONVERSION_OPTIMIZATION",
                        supporting_evidence=[{
                            "source_type": "AIObservation",
                            "attribute_name": obs.attribute_name,
                            "value": obs.attribute_value
                        }],
                        status="ACTIVE",
                        detection_rule="AI_UNCLEAR_VALUE_PROP",
                        detection_timestamp=now_utc
                    )
                )

        # -------------------------------------------------------------
        # D. Digital PR & Publisher Inventory Opportunities
        # -------------------------------------------------------------
        if pub_matches:
            top_pub, top_obs, top_domain = pub_matches[0]
            detected_opps.append(
                SalesOpportunity(
                    company_id=company_id,
                    category="DIGITAL_PR_PUBLISHER",
                    title=f"High-Affinity Publisher Placements Available ({len(pub_matches)} inventory matches)",
                    description=f"Prospect's niche aligns directly with {len(pub_matches)} vetted publishers in ProspectOS inventory (e.g. {top_pub.publisher_name or top_domain}, DA {top_obs.metric_da or 'N/A'}).",
                    severity="MEDIUM",
                    impact_rationale="Securing editorial placements on industry-relevant publications rapidly establishes brand authority and topical trust.",
                    confidence=0.9,
                    recommended_service="DIGITAL_PR",
                    supporting_evidence=[{
                        "source_type": "PublisherRecord",
                        "publisher_name": top_pub.publisher_name,
                        "canonical_domain": top_domain,
                        "metric_da": top_obs.metric_da,
                        "price": top_obs.price,
                        "currency": top_obs.currency
                    }],
                    status="ACTIVE",
                    detection_rule="DIGITAL_PR_INVENTORY_MATCH",
                    detection_timestamp=now_utc
                )
            )

        # -------------------------------------------------------------
        # Persist Detected Opportunities (Upsert / Refresh)
        # -------------------------------------------------------------
        # Remove old opportunities for this company to avoid stale duplicates
        stmt_del = select(SalesOpportunity).where(SalesOpportunity.company_id == company_id)
        old_opps = (await self.session.execute(stmt_del)).scalars().all()
        for opp in old_opps:
            await self.session.delete(opp)

        for opp in detected_opps:
            self.session.add(opp)

        await self.session.commit()
        logger.info(f"Detected {len(detected_opps)} opportunities for company {company_id}")
        return detected_opps

    # =========================================================================
    # 2. Service Fit & Lead Qualification Engine
    # =========================================================================

    def calculate_service_fits(
        self,
        opportunities: List[SalesOpportunity],
        company: Company,
        scan: Optional[WebsiteScan],
        metrics: List[SEOMetric],
        pub_count: int
    ) -> List[Dict[str, Any]]:
        """
        Calculates explainable fit scores (0-100) and rationale for GrokxSEO services.
        Services are only recommended when supported by observed evidence.
        """
        service_scores: Dict[str, float] = {s: 0.0 for s in VALID_GROKXSEO_SERVICES}
        service_rationales: Dict[str, List[str]] = {s: [] for s in VALID_GROKXSEO_SERVICES}
        service_opp_counts: Dict[str, int] = {s: 0 for s in VALID_GROKXSEO_SERVICES}

        for opp in opportunities:
            svc = opp.recommended_service
            if svc in service_scores:
                weight = 35.0 if opp.severity == "CRITICAL" else 25.0 if opp.severity == "HIGH" else 15.0 if opp.severity == "MEDIUM" else 5.0
                service_scores[svc] += weight
                service_rationales[svc].append(opp.title)
                service_opp_counts[svc] += 1

        # Additional contextual boosts
        # Technical SEO
        if scan and ((scan.http_status != 200 and scan.http_status != 403) or not scan.https_enabled):
            service_scores["TECHNICAL_SEO"] = max(service_scores["TECHNICAL_SEO"], 80.0)
            service_rationales["TECHNICAL_SEO"].append("Critical server or SSL protocol failure detected")

        # Link building
        dr_metric = next((m for m in metrics if m.metric_name.lower() in ["domain_rating", "dr"]), None)
        if dr_metric and dr_metric.metric_value is not None and dr_metric.metric_value < 30.0:
            service_scores["LINK_BUILDING"] = max(service_scores["LINK_BUILDING"], 75.0)
            service_rationales["LINK_BUILDING"].append(f"Domain rating is {dr_metric.metric_value:.1f} (< 30 baseline)")

        # Digital PR
        if pub_count > 0:
            service_scores["DIGITAL_PR"] = max(service_scores["DIGITAL_PR"], 65.0)
            service_rationales["DIGITAL_PR"].append(f"{pub_count} relevant media publishers available in current inventory")

        # SEO Strategy
        if len(opportunities) >= 3:
            service_scores["SEO_STRATEGY"] = max(service_scores["SEO_STRATEGY"], 70.0)
            service_rationales["SEO_STRATEGY"].append("Multiple cross-discipline deficits require cohesive roadmap")

        results = []
        for svc, score in service_scores.items():
            normalized_score = min(score, 100.0)
            if normalized_score > 0:
                rationale_text = "; ".join(service_rationales[svc][:3]) if service_rationales[svc] else "Contextual fit based on prospect profile"
                results.append({
                    "service_name": svc,
                    "fit_score": round(normalized_score, 1),
                    "rationale": rationale_text,
                    "supporting_opportunities_count": service_opp_counts[svc]
                })

        # Sort descending by fit score
        results.sort(key=lambda x: x["fit_score"], reverse=True)
        return results

    # =========================================================================
    # 3. Explainable Priority Scoring Model (v3.0.0)
    # =========================================================================

    async def calculate_priority_score(self, company_id: uuid.UUID) -> SalesIntelligenceScore:
        """
        Computes transparent, versioned priority score with component breakdown,
        weights, positive indicators, limitations, and missing information.
        """
        company = await self.session.get(Company, company_id)
        if not company:
            raise ValueError(f"Company {company_id} not found")

        # Detect/refresh opportunities
        opportunities = await self.detect_opportunities(company_id)

        # Fetch scan, metrics, observations
        stmt_scan = select(WebsiteScan).where(WebsiteScan.company_id == company_id).order_by(desc(WebsiteScan.scanned_at)).limit(1)
        scan = (await self.session.execute(stmt_scan)).scalar_one_or_none()

        stmt_metrics = select(SEOMetric).where(SEOMetric.company_id == company_id)
        metrics = (await self.session.execute(stmt_metrics)).scalars().all()

        stmt_obs = select(AIObservation).where(AIObservation.company_id == company_id)
        observations = (await self.session.execute(stmt_obs)).scalars().all()

        # Check publisher matches
        industry_query = company.industry or ""
        stmt_pub = select(func.count(PublisherRecord.id))
        if industry_query:
            stmt_pub = stmt_pub.where(PublisherRecord.audience_focus.ilike(f"%{industry_query}%"))
        pub_count = (await self.session.execute(stmt_pub)).scalar() or 0

        # Component 1: SEO Severity Score (0 - 100)
        # Severity weights: CRITICAL=40, HIGH=25, MEDIUM=15, LOW=5
        raw_severity = 0.0
        for opp in opportunities:
            if opp.severity == "CRITICAL":
                raw_severity += 40.0
            elif opp.severity == "HIGH":
                raw_severity += 25.0
            elif opp.severity == "MEDIUM":
                raw_severity += 15.0
            else:
                raw_severity += 5.0
        seo_severity_score = min(raw_severity, 100.0)

        # Component 2: Service Fit Score (0 - 100)
        service_fits = self.calculate_service_fits(opportunities, company, scan, metrics, pub_count)
        primary_service = service_fits[0]["service_name"] if service_fits else "SEO_STRATEGY"
        service_fit_score = service_fits[0]["fit_score"] if service_fits else 30.0

        # Component 3: Publisher Fit Score (0 - 100)
        publisher_fit_score = min(pub_count * 15.0, 100.0)

        # Component 4: Business Fit Score (0 - 100)
        business_fit = 50.0 # base score for discovered business
        if company.industry:
            business_fit += 20.0
        if company.target_market:
            business_fit += 15.0
        if company.website_url:
            business_fit += 15.0
        business_fit_score = min(business_fit, 100.0)

        # Component 5: Evidence Confidence & Data Completeness (0.0 - 1.0)
        signals_present = 0.0
        signals_total = 4.0 # Scan, SEO Metrics, AI Observations, Publisher Inventory
        is_scan_blocked = False
        if scan:
            if scan.http_status == 403 or scan.scan_status == "ACCESS_RESTRICTED":
                is_scan_blocked = True
                signals_present += 0.5  # Partial: reachability checked, but on-page content blocked
            elif scan.http_status == 200:
                signals_present += 1.0
            else:
                signals_present += 0.5
        if len(metrics) > 0:
            signals_present += 1.0
        if len(observations) > 0:
            verified_obs = [o for o in observations if getattr(o, "verification_status", None) == "VERIFIED"]
            if verified_obs:
                signals_present += 1.0
            else:
                signals_present += 0.5
        if pub_count > 0:
            signals_present += 1.0

        data_completeness = round(signals_present / signals_total, 2)
        confidence_base = 0.5
        if data_completeness >= 0.75:
            confidence_base = 0.95
        elif data_completeness >= 0.5:
            confidence_base = 0.75 if is_scan_blocked else 0.8
        elif data_completeness >= 0.25:
            confidence_base = 0.60
        evidence_confidence_score = round(confidence_base, 2)

        # -------------------------------------------------------------
        # Overall Priority Score Calculation
        # Weights: SEO Severity (35%), Service Fit (25%), Publisher Fit (20%), Business Fit (10%), Confidence (10%)
        # -------------------------------------------------------------
        weights = DEFAULT_SCORING_WEIGHTS
        weighted_score = (
            (seo_severity_score * weights["seo_severity"]) +
            (service_fit_score * weights["service_fit"]) +
            (publisher_fit_score * weights["publisher_fit"]) +
            (business_fit_score * weights["business_fit"]) +
            ((evidence_confidence_score * 100.0) * weights["evidence_confidence"])
        )
        overall_priority_score = round(min(max(weighted_score, 0.0), 100.0), 1)

        # Explainability: Positive Indicators
        positive_indicators = []
        if seo_severity_score >= 60.0:
            positive_indicators.append(f"Significant remediable SEO opportunities detected ({len(opportunities)} items)")
        if service_fit_score >= 70.0:
            positive_indicators.append(f"Strong service alignment with GrokxSEO {primary_service.replace('_', ' ')}")
        if pub_count > 0:
            positive_indicators.append(f"Immediate Digital PR placement opportunities ({pub_count} matching publishers)")
        if company.industry:
            positive_indicators.append(f"Well-defined market vertical: {company.industry}")

        # Explainability: Limitations & Missing Information
        limitations = []
        missing_information = []
        if not scan:
            limitations.append("Missing live website scan data")
            missing_information.append("Website crawl signals (HTTP, SSL, meta tags)")
        elif is_scan_blocked:
            limitations.append("Direct website crawling blocked by bot protection (HTTP 403 / Cloudflare WAF)")
            missing_information.append("Direct on-page SEO signals (H1, title length, meta description, body copy) unverified")
        if len(metrics) == 0:
            limitations.append("No third-party SEO provider metrics configured")
            missing_information.append("Domain Authority, Backlinks, Organic Traffic")
        if len(observations) == 0:
            missing_information.append("AI Qualitative Observations (content quality, value proposition)")
        if pub_count == 0:
            limitations.append("No industry-specific publishers currently cataloged in local inventory")

        # Recommended Next Action
        if not scan:
            recommended_next_action = "Initiate Website Crawl to evaluate technical signals"
        elif seo_severity_score >= 75.0:
            recommended_next_action = f"Generate Sales Intelligence Brief & pitch {primary_service.replace('_', ' ')}"
        elif pub_count > 0:
            recommended_next_action = "Create Media Plan proposal using matched publisher inventory"
        else:
            recommended_next_action = "Review prospect qualification notes and schedule discovery call"

        # -------------------------------------------------------------
        # Upsert SalesIntelligenceScore
        # -------------------------------------------------------------
        stmt_existing = select(SalesIntelligenceScore).where(SalesIntelligenceScore.company_id == company_id)
        existing_score = (await self.session.execute(stmt_existing)).scalar_one_or_none()

        is_new_or_changed = (existing_score is None) or (abs(existing_score.overall_priority_score - overall_priority_score) > 0.01)

        now_utc = self._get_utc_now()
        if existing_score:
            existing_score.scoring_version = SCORING_VERSION
            existing_score.overall_priority_score = overall_priority_score
            existing_score.seo_severity_score = round(seo_severity_score, 1)
            existing_score.service_fit_score = round(service_fit_score, 1)
            existing_score.publisher_fit_score = round(publisher_fit_score, 1)
            existing_score.business_fit_score = round(business_fit_score, 1)
            existing_score.evidence_confidence_score = evidence_confidence_score
            existing_score.data_completeness = data_completeness
            existing_score.primary_recommended_service = primary_service
            existing_score.recommended_services = service_fits
            existing_score.positive_indicators = positive_indicators
            existing_score.limitations = limitations
            existing_score.missing_information = missing_information
            existing_score.component_weights = weights
            existing_score.recommended_next_action = recommended_next_action
            existing_score.evaluated_at = now_utc
            existing_score.updated_at = now_utc
            score_obj = existing_score
        else:
            score_obj = SalesIntelligenceScore(
                company_id=company_id,
                scoring_version=SCORING_VERSION,
                overall_priority_score=overall_priority_score,
                seo_severity_score=round(seo_severity_score, 1),
                service_fit_score=round(service_fit_score, 1),
                publisher_fit_score=round(publisher_fit_score, 1),
                business_fit_score=round(business_fit_score, 1),
                evidence_confidence_score=evidence_confidence_score,
                data_completeness=data_completeness,
                primary_recommended_service=primary_service,
                recommended_services=service_fits,
                positive_indicators=positive_indicators,
                limitations=limitations,
                missing_information=missing_information,
                component_weights=weights,
                recommended_next_action=recommended_next_action,
                review_status="UNREVIEWED",
                evaluated_at=now_utc,
                created_at=now_utc,
                updated_at=now_utc
            )
            self.session.add(score_obj)

        # Record evaluation in CRMActivity to preserve full scoring history timeline
        if is_new_or_changed:
            eval_act = CRMActivity(
                company_id=company_id,
                activity_type="SCORE_EVALUATION",
                actor="system_scorer",
                title=f"Sales Priority Evaluated: {overall_priority_score:.1f} ({primary_service.replace('_', ' ')})",
                details={
                    "scoring_version": SCORING_VERSION,
                    "overall_priority_score": overall_priority_score,
                    "seo_severity_score": round(seo_severity_score, 1),
                    "service_fit_score": round(service_fit_score, 1),
                    "publisher_fit_score": round(publisher_fit_score, 1),
                    "business_fit_score": round(business_fit_score, 1),
                    "evidence_confidence_score": evidence_confidence_score,
                    "primary_service": primary_service,
                    "timestamp": now_utc.isoformat()
                },
                created_at=now_utc
            )
            self.session.add(eval_act)

        await self.session.commit()
        await self.session.refresh(score_obj)
        logger.info(f"Evaluated sales intelligence score {score_obj.overall_priority_score} for company {company_id}")
        return score_obj

    # =========================================================================
    # 4. Sales Intelligence Briefs
    # =========================================================================

    async def generate_or_get_brief(self, company_id: uuid.UUID, force_regenerate: bool = False) -> SalesBrief:
        """
        Generates or retrieves a structured, editable Sales Intelligence Brief.
        Embeds company facts, top opportunities, service fits, publisher matches,
        discovery questions, and Markdown export copy.
        """
        stmt_brief = select(SalesBrief).where(SalesBrief.company_id == company_id)
        brief = (await self.session.execute(stmt_brief)).scalar_one_or_none()

        if brief and not force_regenerate and brief.is_customized:
            return brief

        company = await self.session.get(Company, company_id)
        if not company:
            raise ValueError(f"Company {company_id} not found")

        score = await self.calculate_priority_score(company_id)
        opportunities = await self.detect_opportunities(company_id)

        # Publisher matches
        industry_query = company.industry or ""
        stmt_pub = (
            select(PublisherRecord, PublisherObservation, Company.canonical_domain)
            .join(PublisherObservation, PublisherObservation.publisher_id == PublisherRecord.id)
            .join(Company, Company.id == PublisherRecord.company_id)
            .order_by(desc(PublisherObservation.observation_timestamp))
            .limit(3)
        )
        if industry_query:
            stmt_pub = stmt_pub.where(PublisherRecord.audience_focus.ilike(f"%{industry_query}%"))
        pub_rows = (await self.session.execute(stmt_pub)).all()
        matched_publishers = [
            {
                "publisher_name": pub.publisher_name or pub_domain or "Authorized Publisher",
                "canonical_domain": pub_domain,
                "da": obs.metric_da,
                "dr": obs.metric_dr,
                "price": obs.price,
                "currency": obs.currency or "USD"
            }
            for pub, obs, pub_domain in pub_rows
        ]

        top_opportunities = [
            {
                "category": opp.category,
                "title": opp.title,
                "severity": opp.severity,
                "description": opp.description,
                "recommended_service": opp.recommended_service
            }
            for opp in sorted(opportunities, key=lambda x: (x.severity == "CRITICAL", x.severity == "HIGH", x.severity == "MEDIUM"), reverse=True)[:5]
        ]

        # Discovery questions tailored to observed gaps
        discovery_questions = []
        if any(o.category == "TECHNICAL_SEO" for o in opportunities):
            discovery_questions.append("How frequently does your engineering team audit site performance, SSL, and crawl errors?")
        if any(o.category == "BACKLINK_AUTHORITY" for o in opportunities):
            discovery_questions.append("What is your current strategy for earning editorial mentions and high-authority backlinks in your niche?")
        if any(o.category == "CONTENT_COVERAGE" for o in opportunities):
            discovery_questions.append("How do you currently benchmark your content depth and topical coverage against competitors in SERPs?")
        if matched_publishers:
            discovery_questions.append(f"Have you considered targeted Digital PR placements on industry publications like {matched_publishers[0]['publisher_name']}?")
        discovery_questions.append("What are your primary organic customer acquisition targets for the upcoming quarter?")

        # Construct full Markdown document
        company_name = company.company_name or company.canonical_domain or "Prospect"
        markdown_text = f"""# Sales Intelligence Brief: {company_name}

**Domain:** {company.canonical_domain or 'N/A'}  
**Industry:** {company.industry or 'Unspecified'}  
**Priority Score:** {score.overall_priority_score}/100 (Primary Service: {score.primary_recommended_service.replace('_', ' ')})  
**Evaluation Date:** {score.evaluated_at.strftime('%B %d, %Y')}  

---

## 1. Company Overview
{company_name} operates in the {company.industry or 'technology'} vertical. Currently classified under sales stage `{company.sales_stage}` with an evidence completeness score of {int(score.data_completeness * 100)}%.

## 2. Key SEO Findings & Observed Deficits
{'; '.join(score.positive_indicators) if score.positive_indicators else 'Standard baseline observed.'}

### Top Opportunities
"""
        for i, opp in enumerate(top_opportunities, 1):
            markdown_text += f"{i}. **[{opp['severity']}] {opp['title']}**: {opp['description']}\n"

        markdown_text += f"""
## 3. Recommended GrokxSEO Services
- **Primary:** `{score.primary_recommended_service.replace('_', ' ')}`
"""
        if score.recommended_services:
            for s in score.recommended_services[:3]:
                markdown_text += f"  - **{s['service_name'].replace('_', ' ')}** (Fit Score: {s['fit_score']}): {s['rationale']}\n"

        if matched_publishers:
            markdown_text += "\n## 4. Matched Publisher Placements\n"
            for p in matched_publishers:
                markdown_text += f"- **{p['publisher_name']}** (DA {p['da'] or 'N/A'}, Est. ${p['price'] or 0:,.2f} {p['currency']})\n"

        markdown_text += f"""
## 5. Strategic Sales Discovery Questions
"""
        for q in discovery_questions:
            markdown_text += f"- {q}\n"

        markdown_text += f"""
## 6. Recommended Next Action
{score.recommended_next_action}
"""

        now_utc = self._get_utc_now()
        brief_title = f"Sales Intelligence Brief — {company_name}"

        if brief:
            brief.title = brief_title
            brief.company_overview = f"{company_name} operates in the {company.industry or 'unspecified'} vertical."
            brief.seo_findings_summary = f"{len(opportunities)} verified opportunities detected across site scan and authority metrics."
            brief.top_opportunities = top_opportunities
            brief.recommended_services = score.recommended_services
            brief.matched_publishers = matched_publishers
            brief.data_gaps = score.missing_information
            brief.discovery_questions = discovery_questions
            brief.recommended_next_action = score.recommended_next_action
            brief.full_brief_markdown = markdown_text
            brief.updated_at = now_utc
            brief_obj = brief
        else:
            brief_obj = SalesBrief(
                company_id=company_id,
                title=brief_title,
                company_overview=f"{company_name} operates in the {company.industry or 'unspecified'} vertical.",
                seo_findings_summary=f"{len(opportunities)} verified opportunities detected across site scan and authority metrics.",
                top_opportunities=top_opportunities,
                recommended_services=score.recommended_services,
                matched_publishers=matched_publishers,
                data_gaps=score.missing_information,
                discovery_questions=discovery_questions,
                recommended_next_action=score.recommended_next_action,
                full_brief_markdown=markdown_text,
                is_customized=False,
                created_at=now_utc,
                updated_at=now_utc
            )
            self.session.add(brief_obj)

        await self.session.commit()
        await self.session.refresh(brief_obj)
        logger.info(f"Generated brief for company {company_id}")
        return brief_obj

    # =========================================================================
    # 5. Prioritized Sales Queue
    # =========================================================================

    async def get_prioritized_queue(
        self,
        industry: Optional[str] = None,
        primary_service: Optional[str] = None,
        min_score: Optional[float] = None,
        review_status: Optional[str] = None,
        sales_stage: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[int, List[PrioritizedProspectItem]]:
        """
        Retrieves the prioritized sales queue ordered by effective priority score descending.
        """
        stmt = (
            select(
                Company,
                SalesIntelligenceScore,
                func.count(SalesOpportunity.id).label("total_opps")
            )
            .outerjoin(SalesIntelligenceScore, SalesIntelligenceScore.company_id == Company.id)
            .outerjoin(SalesOpportunity, SalesOpportunity.company_id == Company.id)
            .group_by(Company.id, SalesIntelligenceScore.id)
        )

        if industry:
            stmt = stmt.where(Company.industry.ilike(f"%{industry}%"))
        if sales_stage:
            stmt = stmt.where(Company.sales_stage == sales_stage.upper())
        if primary_service:
            stmt = stmt.where(SalesIntelligenceScore.primary_recommended_service == primary_service)
        if review_status:
            stmt = stmt.where(SalesIntelligenceScore.review_status == review_status.upper())
        if min_score is not None:
            stmt = stmt.where(
                or_(
                    SalesIntelligenceScore.human_override_score >= min_score,
                    SalesIntelligenceScore.overall_priority_score >= min_score
                )
            )

        # Order by effective priority score descending (fallback to 0.0 if not evaluated)
        effective_score_expr = func.coalesce(
            SalesIntelligenceScore.human_override_score,
            SalesIntelligenceScore.overall_priority_score,
            0.0
        )
        stmt = stmt.order_by(desc(effective_score_expr), desc(Company.created_at))

        # Total count
        count_stmt = select(func.count(Company.id))
        if industry:
            count_stmt = count_stmt.where(Company.industry.ilike(f"%{industry}%"))
        if sales_stage:
            count_stmt = count_stmt.where(Company.sales_stage == sales_stage.upper())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        # Execute paginated query
        rows = (await self.session.execute(stmt.offset(offset).limit(limit))).all()

        items = []
        for comp, score_obj, total_opps in rows:
            eff_score = score_obj.human_override_score if score_obj and score_obj.human_override_score is not None else (score_obj.overall_priority_score if score_obj else 0.0)
            items.append(
                PrioritizedProspectItem(
                    company_id=comp.id,
                    company_name=comp.company_name or comp.canonical_domain or "Unnamed Prospect",
                    canonical_domain=comp.canonical_domain,
                    website_url=comp.website_url,
                    industry=comp.industry,
                    target_market=comp.target_market,
                    sales_stage=comp.sales_stage or "NEW",
                    overall_priority_score=score_obj.overall_priority_score if score_obj else 0.0,
                    effective_score=eff_score,
                    has_human_override=score_obj.human_override_score is not None if score_obj else False,
                    seo_severity_score=score_obj.seo_severity_score if score_obj else 0.0,
                    service_fit_score=score_obj.service_fit_score if score_obj else 0.0,
                    publisher_fit_score=score_obj.publisher_fit_score if score_obj else 0.0,
                    evidence_confidence_score=score_obj.evidence_confidence_score if score_obj else 0.0,
                    primary_recommended_service=score_obj.primary_recommended_service if score_obj else None,
                    total_opportunities=total_opps,
                    critical_opportunities_count=0, # Computed if details requested
                    matched_publishers_count=0,
                    review_status=score_obj.review_status if score_obj else "UNREVIEWED",
                    evaluated_at=score_obj.evaluated_at if score_obj else None
                )
            )

        return total, items

    # =========================================================================
    # 6. Human Override & Status Updating
    # =========================================================================

    async def override_score(self, company_id: uuid.UUID, score: float, reason: str, actor: str = "human_reviewer") -> SalesIntelligenceScore:
        score_obj = await self.calculate_priority_score(company_id)
        now_utc = self._get_utc_now()

        old_score = score_obj.human_override_score if score_obj.human_override_score is not None else score_obj.overall_priority_score
        score_obj.human_override_score = score
        score_obj.human_override_reason = reason
        score_obj.human_override_by = actor
        score_obj.human_override_at = now_utc
        score_obj.updated_at = now_utc

        # Log into CRMActivity audit timeline
        act = CRMActivity(
            company_id=company_id,
            activity_type="SCORE_OVERRIDE",
            actor=actor,
            title=f"Sales Intelligence Priority Override: {old_score:.1f} -> {score:.1f}",
            details={
                "old_score": old_score,
                "new_score": score,
                "reason": reason,
                "timestamp": now_utc.isoformat()
            },
            created_at=now_utc
        )
        self.session.add(act)

        await self.session.commit()
        await self.session.refresh(score_obj)
        logger.info(f"Recorded score override for company {company_id}: {old_score} -> {score} by {actor}")
        return score_obj

    async def update_review_status(
        self,
        company_id: uuid.UUID,
        status: Optional[str] = None,
        notes: Optional[str] = None,
        actor: str = "human_reviewer",
        review_status: Optional[str] = None,
        reviewer: Optional[str] = None
    ) -> SalesIntelligenceScore:
        target_status = status or review_status
        target_actor = reviewer or actor
        if not target_status or target_status.upper() not in VALID_REVIEW_STATUSES:
            raise ValueError(f"Invalid review status '{target_status}'. Must be one of: {', '.join(VALID_REVIEW_STATUSES)}")

        score_obj = await self.calculate_priority_score(company_id)
        now_utc = self._get_utc_now()

        old_status = score_obj.review_status
        score_obj.review_status = target_status.upper()
        score_obj.updated_at = now_utc

        act = CRMActivity(
            company_id=company_id,
            activity_type="REVIEW_STATUS_UPDATE",
            actor=target_actor,
            title=f"Lead Review Status: {old_status} -> {target_status.upper()}",
            details={
                "old_status": old_status,
                "new_status": target_status.upper(),
                "notes": notes,
                "timestamp": now_utc.isoformat()
            },
            created_at=now_utc
        )
        self.session.add(act)

        await self.session.commit()
        await self.session.refresh(score_obj)
        logger.info(f"Updated review status for company {company_id}: {old_status} -> {target_status.upper()} by {target_actor}")
        return score_obj

    # =========================================================================
    # 7. Prospect Comparison Side-by-Side
    # =========================================================================

    async def compare_prospects(self, company_ids: List[uuid.UUID]) -> ProspectComparisonResponse:
        compared_list = []
        for cid in company_ids[:5]: # Max 5 prospects
            comp = await self.session.get(Company, cid)
            if not comp:
                continue
            score = await self.calculate_priority_score(cid)
            opps = await self.detect_opportunities(cid)
            brief = await self.generate_or_get_brief(cid)

            compared_list.append(
                ProspectComparisonDetail(
                    company_id=comp.id,
                    company_name=comp.company_name or comp.canonical_domain,
                    canonical_domain=comp.canonical_domain,
                    industry=comp.industry,
                    sales_stage=comp.sales_stage or "NEW",
                    score=SalesIntelligenceScoreResponse.model_validate(score),
                    opportunities=[OpportunityItemResponse.model_validate(o) for o in opps],
                    top_matched_publishers=brief.matched_publishers or [],
                    brief_overview=brief.company_overview
                )
            )

        return ProspectComparisonResponse(compared_prospects=compared_list)
