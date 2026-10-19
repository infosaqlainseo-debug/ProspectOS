# Architectural Decisions Log

## [2026-10-11] Phase 3.4: Automated Reporting & Client Portals
**Decision 1:** Role-Based Authentication & Cryptographic Security: Implemented salted PBKDF2-HMAC-SHA256 password hashing (100,000 iterations, constant-time `hmac.compare_digest`) and signed HS256 JWT access tokens across three discrete roles (`ADMIN`, `AGENCY_STAFF`, `CLIENT_USER`), avoiding external binary dependencies while providing production-grade cryptographic security.
**Decision 2:** Server-Side Multi-Tenant Isolation: Enforced strict tenancy boundaries at the server layer (`enforce_client_isolation`). Any request from a `CLIENT_USER` for data outside their assigned `company_id` is rejected with HTTP 403 Forbidden and automatically recorded in `portal_audit_logs` as an `UNAUTHORIZED_ACCESS_ATTEMPT`. Hiding dashboard components is never assumed to be sufficient authorization.
**Decision 3:** Strict Data Minimization for Client Visibility: Separated client-visible information from internal agency intelligence. Client reports and workspaces strictly exclude wholesale publisher costs, agency margins, internal CRM notes (`CRMNote`), raw lead scores (`SalesIntelligenceScore`), and internal sales stages, exposing only verified technical SEO health, content opportunities, client rate deliverables, and approved media placements.
**Decision 4:** Evidence-Grounded Reporting & Non-Fabrication: Reports are synthesized strictly from stored database records (`WebsiteScan`, `OpportunityProfile`, `MediaPlanItem`, `OutreachDraft`). Where third-party backlink or organic traffic providers are unconfigured, metrics are withheld with prominent disclosure notices rather than fabricated or assumed.
**Decision 5:** Approval Boundary Delivery Safety Gate: Enforced a strict safety barrier requiring explicit agency sign-off (`approval_status == 'APPROVED'`) before any report can be dispatched to external client email recipients. Delivery attempts on unapproved drafts are rejected with HTTP 400 Bad Request.
**Decision 6:** Deterministic Idempotency for Duplicate Delivery Prevention: Guarded against duplicate external email sends during job retries using deterministic daily idempotency keys (`REPORT_{report_id}_{recipient}_{date}`). Delivery attempts matching an existing successful send return the prior log without re-dispatching.
**Decision 7:** Multi-Format Exports & Persistent Audit Logging: Implemented clean Markdown and print-ready HTML export formats with embedded client isolation checks, backed by an append-only audit trail (`portal_audit_logs`) tracking administrative, authentication, and access-control events.

## [2026-10-11] Phase 3.3: Advanced Competitive SEO Intelligence
**Decision 1:** Competitor Discovery via Verified Database Overlap: Grounded candidate competitor discovery strictly in actual database records without inventing competitor names, domains, or traffic metrics. Computed relevance scores from shared industry categorization (up to 40%), sub-industry specialization (up to 15%), and crawl heading/token co-occurrence (up to 35%), tiering candidates deterministically into `DIRECT` (≥0.70), `INDIRECT` (≥0.45), `TOPICAL_PEER` (≥0.25), and `IRRELEVANT` (<0.25).
**Decision 2:** Side-by-Side Multi-Dimensional Crawl Comparisons: Built side-by-side comparisons directly from verified `WebsiteScan` crawl records (word counts, H1 tags, subheadings, SSL, meta descriptions, robots.txt, sitemaps, schema rich snippets, and mobile viewport meta), strictly avoiding synthetic crawl simulations.
**Decision 3:** Search-Intent & Content Gap Mapping: Mapped topical content gaps across standard search intents (`INFORMATIONAL`, `COMMERCIAL`, `TRANSACTIONAL`, `NAVIGATIONAL`), connecting competitor topic coverage directly to actionable GrokxSEO service categories (`CONTENT_STRATEGY`, `CONTENT_ARCHITECTURE`) with explainable effort and impact ratings.
**Decision 4:** Strict Backlink Non-Fabrication: Where third-party backlink providers (Moz, Ahrefs, Semrush) are unconfigured or yield no live data, domain metrics (`prospect_da`, `competitor_da`, `da_differential`) remain `None` (Unknown) rather than defaulting to zero or fabricating dummy authority figures. Explicit limitation notices are embedded in API responses and dashboard banners.
**Decision 5:** Real Publisher Inventory Matching for Digital PR: Matched competitive PR link-building opportunities directly to verified live inventory in `publisher_records` and `publisher_observations` matching the prospect's industry, providing transparent rate cards, currencies, audience focus, and domain metrics without mock data.
**Decision 6:** Deterministic Opportunity Deduplication: Synced competitive intelligence recommendations to `SalesOpportunity` using deterministic rule keys (`COMPETITIVE_GAP_{domain}_{category}`). Repeated analysis runs update existing records in place, completely eliminating duplicate opportunities across modules.
**Decision 7:** Audited History & Executive Overview: Persisted all comparative runs to `competitive_analysis_runs` with immutable timestamps, input scan references, and full diagnostic payloads, enabling historical trend reviews and executive overview aggregations.

## [2026-10-11] Phase 3.2: Revenue & Performance Analytics
**Decision 1:** Strict Separation of Realized Revenue and Pipeline Valuation: Modeled closed-won realized revenue exclusively from deals with `WON` stage/outcome. Active deals contribute strictly to unearned open pipeline valuation, enriched with stage-probability weighting (`DISCOVERY`: 10%, `QUALIFICATION`: 25%, `PROPOSAL`: 50%, `NEGOTIATION`: 75%). Lost deals are excluded from both.
**Decision 2:** Non-Fabrication of Costs & Profitability: Fulfillment costs are derived strictly from verified `CRMDeal.cost_amount` or itemized `MediaPlanItem.proposed_price`. Where costs are unrecorded, costs, gross profit, and gross margins are returned as `None` / unavailable rather than defaulting to zero, preventing false 100% margin calculations. Coverage percentage and limitations are explicitly disclosed.
**Decision 3:** Multi-Currency Handling and Policy Normalization: Un-normalized native totals are preserved per currency alongside normalized USD aggregates. Conversions use a documented benchmark reference table (`USD: 1.0`, `EUR: 1.08`, `GBP: 1.28`, `CAD: 0.74`, `AUD: 0.66`) with baseline sources and timestamps exposed in API metadata.
**Decision 4:** Net Realized Revenue Formulation: Modeled net revenue explicitly as `closed_amount - discount_amount + tax_amount - refunded_amount`, preserving granular audit trails for discounts, taxes, and refunds.
**Decision 5:** Automated Funnel Bottleneck Diagnosis: Evaluated sequential pipeline progression (`DISCOVERY -> QUALIFICATION -> PROPOSAL -> NEGOTIATION -> WON`), computing stage-to-stage transition conversion rates and drop-off rates, and automatically diagnosing the lowest-conversion stage with recommended actions.
**Decision 6:** Correlation-Based Campaign Attribution with Sample Thresholds: Attributed revenue to outreach campaigns via direct deal linkage while explicitly disclosing that causality is not guaranteed. Enforced minimum sample threshold ($N \ge 5$) before classifying ROI as statistically stable.
**Decision 7:** Persistent Snapshot Immutability: Persisted executive analytics snapshots to `revenue_analytics_snapshots` table for historical audit trails, compliance reviews, and immutable point-in-time reporting.

## [2026-10-11] Phase 3.1: Publisher Intelligence & Data Quality Monitoring
**Decision 1:** 4-Dimensional Quality Scoring Model: Evaluated publisher record health across Completeness (25%), Validity (25%), Freshness (30%), and Consistency (20%), establishing clear thresholds: EXCELLENT (90-100), ACCEPTABLE (70-89), POOR (50-69), and CRITICAL (<50).
**Decision 2:** Field-Level Independent Freshness Tracking: Configured distinct freshness half-lives per data type rather than a single monolithic timestamp: pricing data becomes stale after 30 days, domain authority metrics after 60 days, and crawl availability after 14 days. Stale data is never treated as current.
**Decision 3:** Non-Destructive Observations & Immutability: Changes to publisher prices, currencies, and SEO metrics never overwrite historical rows. Updates insert a new `PublisherObservation` row, preserving historical rate cards and audit trails without data loss.
**Decision 4:** Safe Provider Refresh & Non-Fabrication: Refreshes operate strictly through authorized providers (Moz, Ahrefs, internal crawler). When credentials are unconfigured or APIs are rate-limited, the system records `PROVIDER_NOT_CONFIGURED` in `PublisherRefreshLog` and preserves existing observations without fabricating dummy metrics.
**Decision 5:** Audited Human Corrections & Attribution: Manual corrections require mandatory operator justification and user attribution, automatically logging an immutable entry to `CRMActivity` to ensure complete traceability.
**Decision 6:** Matching Engine Integration & Limitations Disclosure: The `MatchingEngine` flags unverified data (`UNVERIFIED` observations) and stale data (>30d prices, >60d metrics) with explicit warnings in `MatchResult.warnings`, ensuring media plan builders communicate data limitations rather than presenting stale data as verified.
**Decision 7:** Non-Destructive Finding Resolution: Finding remediation permits marking findings as `RESOLVED` or `IGNORED` with attributable notes. Prohibited automated destructive record deletion or silent merging to avoid accidental inventory loss.

## [2026-10-11] Phase 3.0: AI Sales Intelligence & Lead Prioritization
**Decision 1:** Granular 8-Category Opportunity Model: Decomposed findings into `TECHNICAL_SEO`, `INDEXABILITY_CRAWLABILITY`, `PAGE_METADATA`, `CONTENT_COVERAGE`, `INTERNAL_LINKING`, `BACKLINK_AUTHORITY`, `COMPETITIVE_GAP`, and `DIGITAL_PR_PUBLISHER` strictly tied to verifiable primary records (`WebsiteScan`, `SEOMetric`, `AIObservation`, `PublisherRecord`).
**Decision 2:** Explainable Priority Scoring v3.0.0: Prioritized leads deterministically using a transparent weighted model: SEO Deficit Severity (35%), GrokxSEO Service Fit (25%), Publisher Alignment (20%), Business Fit (10%), and Evidence Confidence (10%). Prohibited treating missing data as zero or fabricating metrics.
**Decision 3:** Separation of Severity, Service Fit, and Sales Priority: Distinctly separated observed SEO deficit severity, agency service capability fit, and final sales priority in the schema, API, and UI to avoid confusing large technical problems with immediate agency fit.
**Decision 4:** Traceable Opportunity-to-Service Mapping: Built deterministic mappings connecting verified deficits to 10 specific GrokxSEO offerings (Technical SEO, SEO Strategy, Content Strategy, Content Architecture, Link Building, Digital PR, Guest Posting, Local SEO, Conversion Optimization, Website Redesign). Services are never recommended without supporting evidence.
**Decision 5:** Editable Intelligence Briefs with Markdown Export: Generated structured briefs containing verified facts, critical SEO findings, discovery questions, publisher alignments, and next actions. Briefs support live customization while preserving original evidence, and export directly as `.md` files.
**Decision 6:** Human Override Auditing: Enabled sales leadership to override priority scores, mandating a documented reason and actor identity, permanently logging an immutable audit record in `crm_activities`.

## [2026-10-10] Phase 2.5: CRM & Sales Pipeline
**Decision 1:** 11-Stage Sales State Machine: Implemented default configurable pipeline stages (`NEW`, `RESEARCHED`, `QUALIFIED`, `CONTACTED`, `REPLIED`, `MEETING_SCHEDULED`, `PROPOSAL_SENT`, `NEGOTIATION`, `WON`, `LOST`, `NURTURE`) with validated transitions and explicit stage change reasoning.
**Decision 2:** Stage Transition Safeguards: Strictly prohibited automatically moving prospects to `CONTACTED` upon draft generation. Transition to `CONTACTED` requires verified provider-confirmed message delivery or explicit human reviewer action. Deals and prospects are never automatically marked as `WON` without authorized human reviewer action.
**Decision 3:** Separation of Pipeline Value vs. Closed Revenue: Stored estimated open value in `estimated_value` and actual earned revenue upon closure in `closed_amount`. Prohibited aggregating disparate currencies without documented conversion feeds.
**Decision 4:** Idempotent Task Deduplication: Added `idempotency_key` unique constraint to `crm_tasks` to ensure workflow engine retries or repeated user submissions never create duplicate tasks.
**Decision 5:** Immutable CRM Activity Timeline: Modeled append-only `crm_activities` table with `actor`, `activity_type`, and `details` JSONB to preserve a tamper-proof audit log of every stage change, deal won/lost, task completion, and note.
**Decision 6:** Unified Prospect Dossier Architecture: Connected company records to website scans, SEO opportunities, verified contacts, media plans, outreach messages, deals, tasks, notes, and activity timeline in a single aggregation layer (`UnifiedProspectDetail`).

## [2026-10-10] Phase 2.4: AI Outreach Automation
**Decision 1:** Strict Human Approval Gate: Draft generation never sends emails automatically. Explicit human review and approval (`approval_status == 'APPROVED'`) is mandatory before any send call is permitted.
**Decision 2:** 9-Stage Sending Safety Barrier: Before dispatching, the engine validates recipient syntax, draft approval, non-sent state, central opt-out suppression, contact record opt-out, duplicate-send 7-day cooldown, campaign daily send limits, provider readiness, and creates follow-ups strictly in `UNAPPROVED` status.
**Decision 3:** Traceable Evidence Citations & Non-Fabrication: All claims made in generated drafts must carry traceable `evidence_citations` linking back to `WebsiteScan`, `OpportunityProfile`, or `MediaPlan` database records. Missing metrics are never hallucinated.
**Decision 4:** Modular Email Providers with Safe Default: The system defaults to `EMAIL_PROVIDER = "none"` with an `UnconfiguredEmailProvider` safe fallback that prevents accidental sends without explicit provider configuration.
**Decision 5:** Opt-Out Suppression Precedence: Unsubscribe or opt-out requests immediately cancel all pending follow-ups and permanently block future sends across all campaigns for that recipient and domain.

## [2026-10-10] Phase 2.3: Workflow Automation Engine
**Decision 1:** 8-Stage Pipeline with Human Review Boundary: Workflows halt at Stage 8 (`human_review`), requiring explicit reviewer approval before media plans are marked `FINAL`.
**Decision 2:** Persistent State Machine & Isolated Retries: Stage execution progress is tracked in `stage_progress` with per-company failure isolation and exponential backoff retries.

## [2026-10-09] Phase 1.8: Prospect Opportunity Intelligence Engine
**Decision 1:** Rule-based Scoring Engine: Before moving to a predictive AI scoring model, we implement a strict rule-based `OpportunityEngine` based on `SEOMetric`, `WebsiteScan`, and `AIObservation` thresholds to ensure reproducibility and prevent hallucinatory scoring.
**Decision 2:** Transparency in Profiling: The `OpportunityProfile` stores explicit lists of `supporting_evidence` and `identified_problems` so the end-user (or Next.js UI) can display exactly *why* a service was recommended.
**Decision 3:** Confidence and Freshness metrics: The engine computes confidence based on data completeness (amount of signals present) and freshness (timestamp deltas) rather than assuming all data is equally valid.
## [2026-10-08] Phase 1.6: AI Extraction & Validation Layer
**Decision 1:** Generics Validation: We use `Generic[T]` on `AIEvidence` along with Pydantic so that taxonomy (Enum) violations inside nested structures are automatically caught during LLM output parsing, completely stopping hallucinated categories.
**Decision 2:** AI Observation Overwrite rules: `AIObservation` never overwrites `Evidence`. The AI acts as an interpretation engine, placing its results in `AIObservation`, and any clash with verified `Evidence` generates an `AIContradiction` instead of silently wiping the truth.
**Decision 3:** Token Usage Tracking: Tracked natively in `AIExtractionRun` across all requests to map cost linearly.
## [2026-10-08] Phase 1.5: SEO Metric Enrichment Engine
**Decision 1:** API Provider Abstraction: Extracted a base `SEOProvider` that uses standard return types (`ProviderResponse`) regardless of provider internal structures (JSON vs CSV etc.)
**Decision 2:** Graceful Provider Degradation: If one provider rate-limits or times out, the `SEOEnrichmentRunner` strictly catches the exception without halting parallel or sequential evaluations of other providers.
**Decision 3:** Unit Tracking: Designed `ProviderUsage` to store estimated units and counts per provider to avoid unbounded billing surprises in batch queues.
**Decision 4:** Immutability of Records: `SEOMetric` stores the current verified snapshot alongside an immutable append-only `HistoricalSnapshot` and `Evidence` record mapping exactly which endpoint yielded what.
**Decision 5:** Pydantic Validation: Provider metrics map tightly into Pydantic models with explicitly managed statuses (`NOT_AVAILABLE` for unsupported vs `ERROR`).
## [2026-10-08] Phase 1.4: Website Intelligence Engine
**Decision 1:** Parsing Libraries: `httpx` and `BeautifulSoup4` chosen for deterministic metadata extraction (no heavy headless browser required for basic signals).
**Decision 2:** Modular Extraction: Separated extraction logic (`extractor.py`) from HTTP fetching (`client.py`) for testability.
**Decision 3:** Immutability: Every website analysis yields a new `WebsiteScan` snapshot rather than overwriting existing records.
**Decision 4:** Social Profile Verification: Extracted strictly via regex matching on `href` tags in DOM; generated URLs based on names are prohibited.
**Decision 5:** Batch Async Processing: The analysis job is queued per company asynchronously via ARQ to prevent blocking during slow website fetches.

## [2026-10-08] Phase 1.3: Company Discovery
**Decision 1:** Data Sources: Start with structured public APIs (e.g., GitHub Organizations) rather than broad web scraping.
**Decision 2:** Duplication Safety: Reliance on PostgreSQL Unique Constraints for Domain and HTTP canonicalization logic prior to insertion.
**Decision 3:** Extensibility: Added generic `DiscoveryProvider` abstraction so future APIs (LinkedIn, Crunchbase) can be slotted in uniformly.
## [2026-10-08] Phase 1.2: Database & Async Job Infrastructure
**Decision 1:** Backend Language & Frameworks: Python 3.12+ with FastAPI due to robust async support and ML/AI ecosystem.
**Decision 2:** ORM: SQLAlchemy 2.x using `asyncpg` for non-blocking database queries.
**Decision 3:** Migrations: Alembic for schema tracking and reproducibility.
**Decision 4:** Task Queue: ARQ chosen over Celery for a simpler, native async (asyncio) queue backed by Redis.
**Decision 5:** Local Infrastructure: Docker Compose used for PostgreSQL and Redis to ensure reproducible developer environments without hardcoded credentials.

## [2026-10-08] Project Brain & Data Governance
**Decision 1:** PostgreSQL is the persistent source of truth.
**Decision 2:** The LLM is not the source of truth for factual metrics.
**Decision 3:** Evidence/provenance is mandatory for important external facts.
**Decision 4:** Historical observations are preserved.
**Decision 5:** Provider integrations must be modular.
**Decision 6:** Crawler and enrichment jobs must be asynchronous.
**Decision 7:** Phase 1 focuses on data intelligence, not sales automation.

## [2026-10-08] Initial Project Assessment
**Context:** The repository `/Users/muhammadsaqlain/Desktop/ProspectOS` was initially empty. No existing frameworks, databases, or infrastructure were present.

**Decision:**
- Start the project from scratch, establishing a clear separation of concerns between the frontend (UI), backend (API/orchestration), and background workers (scraping/AI agents).
- Emphasize data accuracy, validation, and traceability over rapid UI development, as per the primary objective of preventing hallucinated data.
