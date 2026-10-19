# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [Phase 3.4] - 2026-10-11
### Added
- **Automated Reporting & Client Portals Engine**
  - Added Alembic migration `b8c9d0e1f2a3` creating 6 new PostgreSQL tables: `portal_users`, `client_invitations`, `client_reports`, `report_schedules`, `report_delivery_logs`, and `portal_audit_logs`.
  - Implemented `ReportingAndPortalService` providing:
    - Cryptographic authentication with salted PBKDF2-HMAC-SHA256 password hashing (100,000 iterations, constant-time `hmac.compare_digest`) and signed HS256 JWT access tokens across roles (`ADMIN`, `AGENCY_STAFF`, `CLIENT_USER`).
    - Server-side multi-tenant isolation (`enforce_client_isolation`) strictly binding `CLIENT_USER` accounts to their assigned `company_id`. Any cross-tenant access attempt raises HTTP 403 Forbidden and records an `UNAUTHORIZED_ACCESS_ATTEMPT` audit event.
    - Strict client-visible data minimization: reports and client portal workspaces explicitly exclude wholesale publisher costs, agency profit margins, internal CRM notes (`CRMNote`), raw lead priority scores (`SalesIntelligenceScore`), and internal sales stages.
    - Automated evidence-grounded report synthesis from stored records (`WebsiteScan`, `OpportunityProfile`, `MediaPlanItem`, `OutreachDraft`) generating 7 structured sections (Executive Summary, Technical SEO & Website Health, Content Gaps & Search Intent, Backlinks & Authority Verification, Publisher Placements, Campaign Deliverables, Recommendations).
    - Strict non-fabrication guarantee: where third-party backlink or traffic APIs are unconfigured, metrics are withheld with prominent limitation disclosures rather than estimated or simulated.
    - Delivery safety gate: reports start in `UNAPPROVED` draft status; external dispatch strictly requires agency approval (`approval_status == 'APPROVED'`). Unapproved delivery attempts fail with HTTP 400 Bad Request.
    - Duplicate delivery prevention using deterministic daily idempotency keys (`REPORT_{report_id}_{recipient}_{date}`).
    - Multi-format document exports for clean Markdown and print-ready branded HTML.
    - Cadence scheduling supporting weekly, monthly, and quarterly generation with client time zone configuration and recipient rosters.
    - Append-only security audit trail (`portal_audit_logs`) tracking logins, report creation, approvals, deliveries, invitations, and access attempts.
  - Added REST API at `/portal` with 17 endpoints covering auth, invitations, reports, exports, cadence schedules, client workspace, and audit logs.
  - Registered background worker jobs `scheduled_report_generation_job` and `report_delivery_job` in ARQ worker.
  - Built interactive Next.js dashboards:
    - Agency Reports Manager at `/reports`: overview metrics, report generation wizard, approvals workflow, delivery dispatch with simulation toggle, cadence scheduler, export previewer, and audit log drawer.
    - Client Portal Workspace at `/portal`: client-sanitized overview with crawl health, content pillars, certified deliverables library with HTML/Markdown downloads, team invitation manager, and non-fabrication disclosure banner.
  - Added `FileText` (Client Reports) and `ShieldCheck` (Client Portal) links to frontend sidebar navigation.
  - Added 10 automated tests in `backend/tests/test_client_portal_and_reporting.py` (total test suite passing: 100%).
  - Validated against live production PostgreSQL database records via `validate_client_portal_reporting_real_data.py`.

## [Phase 3.3] - 2026-10-11
### Added
- **Advanced Competitive SEO Intelligence Engine**
  - Added Alembic migration `a7b8c9d0e1f2` creating 2 new PostgreSQL tables: `company_competitors` and `competitive_analysis_runs`.
  - Implemented `CompetitiveIntelligenceService` providing:
    - Competitor discovery based on database industry categorization, sub-industry alignment, and crawl keyword/heading overlap with deterministic relevance scores and tiering (`DIRECT`, `INDIRECT`, `TOPICAL_PEER`, `IRRELEVANT`).
    - Full CRUD competitor relationship tracking with validation status (`VERIFIED`, `UNVERIFIED`), notes, and relevance overrides.
    - Side-by-side crawl and content comparison across word count, heading tags, SSL security, meta descriptions, robots.txt, sitemaps, schema rich snippets, and mobile viewport meta.
    - Search-intent categorized topical content gap analysis (`INFORMATIONAL`, `COMMERCIAL`, `TRANSACTIONAL`, `NAVIGATIONAL`), mapping deficits directly to GrokxSEO service offerings (`CONTENT_STRATEGY`, `CONTENT_ARCHITECTURE`).
    - Technical SEO issue identification with severity (`HIGH`, `MEDIUM`, `LOW`), concrete evidence, and remediation actions.
    - Internal linking and silo architecture analysis detecting shallow cluster depth and lack of structured sub-pages.
    - Strict non-fabrication of backlink metrics: where third-party providers (Moz, Ahrefs, Semrush) are unconfigured, authority values remain `None` (Unknown) rather than defaulting to zero or fabricating dummy numbers, with explicit disclosures in limitations.
    - Digital PR and publisher opportunity matching directly linked to live `publisher_records` and `publisher_observations` matching the prospect's industry.
    - Prioritized GrokxSEO recommendations ranked by priority score (0-100), effort, impact, and confidence.
    - Deterministic opportunity deduplication syncing recommendations into `SalesOpportunity` with unique rule keys (`COMPETITIVE_GAP_{domain}_{category}`), eliminating duplicate records across re-runs.
  - Added REST API at `/competitive` with 8 endpoints:
    - `POST /competitive/companies/{company_id}/discover`
    - `GET /competitive/companies/{company_id}/competitors`
    - `POST /competitive/companies/{company_id}/competitors`
    - `PUT /competitive/competitors/{competitor_id}`
    - `POST /competitive/companies/{company_id}/analyze`
    - `GET /competitive/companies/{company_id}/runs`
    - `GET /competitive/companies/{company_id}/runs/latest`
    - `GET /competitive/runs/{run_id}`
    - `GET /competitive/companies/{company_id}/overview`
  - Registered worker background job `competitive_analysis_job` in ARQ worker.
  - Built interactive Next.js Dashboard at `/competitive-intelligence` featuring prospect selector, candidate discovery drawer, manual competitor tracking modal, executive overview metrics, and multi-tab side-by-side diagnostic explorer (Executive Overview, Topical Content Gaps, Technical SEO, Silos & Linking, Authority & Backlinks, Digital PR Placements, Prioritized Recommendations, and Historical Runs).
  - Added `Swords` Competitive SEO link to frontend sidebar navigation.
  - Added 4 automated tests in `backend/tests/test_competitive_intelligence.py` (total test suite: 72/72 passing).
  - Validated against production PostgreSQL database records via `validate_competitive_intelligence_real_data.py`.

## [Phase 3.2] - 2026-10-11
### Added
- **Revenue & Performance Analytics Engine**
  - Added Alembic migration `f6a7b8c9d0e1` adding financial fidelity columns to `crm_deals` (`campaign_id`, `cost_amount`, `invoice_status`, `invoiced_amount`, `paid_amount`, `discount_amount`, `tax_amount`, `refunded_amount`) and creating persistent table `revenue_analytics_snapshots`.
  - Implemented `RevenueAnalyticsService` calculating realized won revenue, strictly separated open pipeline value, stage-probability-weighted pipeline value, sales cycle duration, and win rates using existing CRM records as the single source of truth.
  - Implemented financial correctness safeguards: Net realized revenue formula (`closed_amount - discount_amount + tax_amount - refunded_amount`), un-normalized native currency totals preserved alongside USD aggregates via documented benchmark exchange rate reference table.
  - Implemented non-fabrication of fulfillment costs and gross profit margins: costs, gross profit, and gross margins are reported as `None` when cost data is unrecorded, avoiding false 100% margin calculations and explicitly disclosing cost coverage percentages and data limitations.
  - Implemented automated sales funnel analysis across sequential stages (`DISCOVERY -> QUALIFICATION -> PROPOSAL -> NEGOTIATION -> WON` + `LOST`), computing stage-to-stage transition conversion rates, drop-offs, and diagnosing pipeline bottlenecks with remedial recommendations.
  - Implemented campaign ROI analysis with explicit correlation disclosures and minimum sample thresholds ($N \ge 5$).
  - Implemented persistent snapshots (`RevenueAnalyticsSnapshot`) stored in PostgreSQL for immutable historical audit trails and point-in-time executive reviews.
  - Added REST API at `/analytics` with 9 endpoints: `/revenue`, `/services`, `/clients`, `/campaigns`, `/funnel`, `/trends`, `/drilldown/deals`, and `/snapshots` (POST, GET).
  - Built interactive Next.js Dashboard at `/analytics` with executive KPI summary cards, filter bars (period presets, date ranges, service category, native currency), interactive tabs for historical trends, sales funnel bottlenecks, service/client leaderboards, campaign ROI, paginated deals ledger with calculation provenance, and persistent snapshot capture modal.
  - Added `BarChart3` Revenue Analytics link to frontend sidebar navigation.
  - Added 8 automated tests in `backend/tests/test_revenue_analytics.py` (total test suite passing: 100%).
  - Validated against production PostgreSQL database records via `validate_revenue_analytics_real_data.py`.

## [Phase 3.1] - 2026-10-11
### Added
- **Publisher Intelligence & Data Quality Monitoring Engine**
  - Added Alembic migration `e5f6a7b8c9d0` creating 3 new PostgreSQL tables: `publisher_quality_scores`, `publisher_quality_findings`, and `publisher_refresh_logs`.
  - Implemented `PublisherQualityScore` computing 4 distinct quality dimensions: Completeness (presence of price, currency, SEO metrics, crawl), Validity (URL syntax, RFC domain normalization, valid positive pricing, supported currency ISO codes), Freshness (field-level tracking: prices stale after 30d, SEO metrics stale after 60d, site status stale after 14d), and Consistency (canonical domain matching, conflicting historical pricing).
  - Implemented `PublisherQualityFinding` detection identifying missing, stale, invalid, duplicate, and conflicting publisher records with severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`), evidence JSON payloads, and recommended actions.
  - Implemented non-destructive updates and historical observation preservation: manual corrections and provider refreshes append new `PublisherObservation` entries (`HUMAN_VERIFIED` or `VERIFIED`) without deleting or overwriting past observations.
  - Added audited human correction workflow logging attributable changes to `CRMActivity` with operator identity and mandatory justification.
  - Added safe finding resolution workflow allowing reviewers to mark findings `RESOLVED` or `IGNORED` with attributable audit notes.
  - Implemented safe provider refresh strictly through authorized and available sources (Moz/Ahrefs) with fallback handling for unconfigured credentials without metric fabrication.
  - Integrated publisher matching engine (`MatchingEngine`) to recognize unverified data and stale observations (>30d price, >60d metrics), generating explicit quality warnings in match results.
  - Added full REST API at `/publishers` with quality endpoints: `/quality/summary`, `/quality/findings`, `/quality/audit`, `/quality/batch-audit`, `/{id}/quality`, `/{id}/refresh`, `/{id}/manual-correction`, `/findings/{id}/resolve`, and `/refresh/logs`.
  - Registered background worker jobs `publisher_quality_audit_job` and `publisher_refresh_job` in ARQ worker.
  - Built interactive Next.js Dashboard at `/publishers` featuring KPI summary cards, filterable Inventory Directory with quality indicators, reviewable Findings table, Provider Refresh logs, and slide-out Inspection Drawer with field-level freshness meters, observation timeline, manual correction modal, and finding resolution modal.
  - Added 9 automated tests in `backend/tests/test_publisher_quality.py` (total backend test suite: 60/60 passing).
  - Executed real-data end-to-end validation across production PostgreSQL records (2,200 companies, 1,602 publishers, 3,533 observations).

## [Phase 3.0] - 2026-10-11
### Added
- **AI Sales Intelligence & Lead Prioritization Engine**
  - Added Alembic migration `d4e5f6a7b8c9` creating 3 new PostgreSQL tables: `sales_intelligence_scores`, `sales_opportunities`, and `sales_briefs`.
  - Implemented `SalesOpportunity` detection covering 8 granular categories: `TECHNICAL_SEO`, `INDEXABILITY_CRAWLABILITY`, `PAGE_METADATA`, `CONTENT_COVERAGE`, `INTERNAL_LINKING`, `BACKLINK_AUTHORITY`, `COMPETITIVE_GAP`, and `DIGITAL_PR_PUBLISHER` strictly grounded in verifiable records (`WebsiteScan`, `SEOMetric`, `AIObservation`, `PublisherRecord`).
  - Implemented `SalesIntelligenceScore` engine (`v3.0.0`) with explainable weighted multi-factor scoring: SEO Deficit Severity (35%), GrokxSEO Service Fit (25%), Publisher Alignment (20%), Business Fit (10%), and Evidence Confidence (10%).
  - Added transparent qualification model distinguishing directly observed deficits from estimations, reporting explicit data gaps and missing providers without fabricating keyword volumes, traffic, or revenues.
  - Implemented opportunity-to-service mapping for 10 core GrokxSEO offerings: Technical SEO, SEO Strategy, Content Strategy, Content Architecture, Link Building & Authority, Digital PR, Guest Posting, Local SEO, Conversion Optimization, and Website Redesign.
  - Built `SalesBrief` generator creating structured, editable Markdown dossiers with verified company facts, critical SEO findings, service recommendations with rationale, publisher inventory alignments, data gaps, strategic discovery questions, and next actions.
  - Added full REST API at `/sales-intelligence` with 9 endpoints: `/queue`, `/prospects/{id}/score`, `/prospects/{id}/evaluate`, `/prospects/{id}/opportunities`, `/prospects/{id}/brief` (GET, PUT, export), `/prospects/{id}/override`, `/prospects/{id}/review-status`, `/compare`, and `/batch/evaluate`.
  - Registered background worker job `sales_intelligence_evaluation_job` in ARQ worker.
  - Added Prioritization Dashboard at `/sales-intelligence` with prioritized queue table, KPI counters, explainable factor drawer, opportunities viewer, Markdown brief editor with export, side-by-side comparison modal, score override modal with audit logging, and quick CRM task creator.
  - Added Target icon and `/sales-intelligence` link to sidebar navigation.
  - Added 6 new automated tests in `backend/tests/test_sales_intelligence.py` (total test suite: 51/51 passing).
  - Validated complete real-data lifecycle with `backend/scripts/validate_sales_intelligence_e2e.py` on real records in PostgreSQL.
### Added
- **CRM & Sales Pipeline System**
  - Added Alembic migration `c3d4e5f6a7b8` altering `companies` (adding `sales_stage`, `target_market`, `qualification_notes`, `stage_updated_at`, `stage_reason`) and creating 4 new tables: `crm_deals`, `crm_tasks`, `crm_activities`, and `crm_notes`.
  - Implemented configurable 11-stage sales pipeline state machine: `NEW`, `RESEARCHED`, `QUALIFIED`, `CONTACTED`, `REPLIED`, `MEETING_SCHEDULED`, `PROPOSAL_SENT`, `NEGOTIATION`, `WON`, `LOST`, `NURTURE`.
  - Enforced stage transition safeguards: `CONTACTED` requires confirmed provider outreach delivery or explicit reviewer action; `WON` requires authorized user action.
  - Implemented `CRMService` with unified 360-degree prospect dossiers, deal revenue management (strict separation of estimated pipeline value vs actual closed earned revenue), idempotent task engine (`idempotency_key` deduplication), internal notes, activity audit timeline, and aggregate reporting metrics.
  - Added REST API at `/crm` mounted in FastAPI with 14 endpoints for Kanban boards, prospect search/filtering, deal management, task tracking, note authoring, and conversion metrics.
  - Extended Next.js frontend with full CRM dashboard at `/crm` (Kanban board, prospect directory, deals & revenue, tasks & follow-ups, conversion reports, and slide-out 360° dossier drawer).
  - Added Kanban icon and `/crm` route to sidebar navigation.
  - Added 6 new automated CRM tests in `backend/tests/test_crm.py` (total test suite: 45/45 passing).
  - Validated complete system with controlled E2E verification script `backend/scripts/validate_crm_e2e.py` on real persisted records.

## [Phase 2.4] - 2026-10-10
### Added
- **AI Outreach Automation System**
  - Added Alembic migration `b2c3d4e5f6a7` creating 5 tables: `company_contacts`, `outreach_campaigns`, `outreach_drafts`, `outreach_messages`, and `outreach_suppressions`.
  - Implemented `ContactResearcher` extracting verified business contacts from website metadata, security.txt, and public pages with provenance and verification confidence (`VERIFIED` vs `INFERRED`).
  - Implemented `OutreachPersonalizationEngine` assembling drafts grounded in `WebsiteScan`, `OpportunityProfile`, and `MediaPlan` with traceable `evidence_citations` and a non-fabrication guarantee for missing metrics.
  - Built `OutreachSenderService` enforcing a 9-stage sending safety barrier: human approval check (`approval_status == 'APPROVED'`), draft un-sent check, RFC syntax validation, opt-out suppression check, contact opt-out check, 7-day duplicate outreach cooldown, campaign daily send limits, provider readiness check, and follow-up sequence scheduling.
  - Added modular `EmailProviderRegistry` with `MockEmailProvider`, `GmailProvider` (OAuth2), `SMTPProvider` (TLS/STARTTLS), and safe `UnconfiguredEmailProvider` fallback (`EMAIL_PROVIDER = "none"`).
  - Implemented REST API at `/outreach` for contacts, campaigns, drafts, approvals, sending, suppressions, message history, and provider status.
  - Added background jobs `outreach_contact_discovery_job` and `outreach_draft_generation_job`.
  - Built interactive Outreach dashboard at `/outreach` with draft cards, live evidence citation drawers, draft editor, campaign manager, contact list, message history, and opt-out suppression controls.
  - Validated complete system with 39/39 passing pytest tests and a 10/10 controlled E2E verification script on real prospect `TechCrunch`.

## [Phase 2.3] - 2026-10-10
### Added
- **Workflow Automation Engine**
  - Implemented 8-stage persistent workflow state machine: `discovery`, `website_analysis`, `seo_enrichment`, `ai_extraction`, `opportunity_scoring`, `publisher_matching`, `media_plan_generation`, `human_review`.
  - Added Alembic migration `a1c2d3e4f5a6` adding `selected_company_ids` and `last_run_at` to `workflows`, and `stage_progress`, `parameters`, `approved_at`, `approved_by` to `workflow_runs`.
  - Extended `WorkflowOrchestrator` with stage ordering, per-company failure isolation, exponential backoff retries, duplicate prevention/idempotency, provider request limits check, and human approval boundary (`approve_workflow_run`, `reject_workflow_run`).
  - Added ARQ background jobs and cron registration: `publisher_matching_job`, `media_plan_generation_job`, and `workflow_scheduler_tick` (cron every minute) using Python `zoneinfo` and cron expression evaluator.
  - Implemented full suite of REST API endpoints in `/workflows`: manual execution with prospect selection, live run inspection, cancellation, retry, approval/rejection, and scheduler tick.
  - Built interactive Next.js dashboard at `/workflows` featuring multi-stage visual pipeline, New Workflow modal, Run Workflow modal with prospect selector, Live Run Inspector, Retry/Cancel controls, and Stage 8 Human Approval controls.
  - Executed controlled end-to-end validation across production PostgreSQL records (1,517 companies, 1,447 publishers, 3,379 observations), generating persisted `MediaPlan` and successfully approving it to `FINAL`.
  - Maintained strict approval boundary: Stage 8 halts automatically at `PENDING_APPROVAL`, awaiting explicit human review; zero external communications or cold emails sent.

## [Phase 2.0] - 2026-10-09
### Added
- **Publisher Inventory Integration & Normalization**
- Implemented `PublisherRecord`, `PublisherObservation`, `ImportBatch`, and `ImportAuditRow` to handle publisher integration linked to the core `Company` model.
- Added `/publishers/import/preview` and `/publishers/import/commit` robust asynchronous endpoints for file uploads mapping.
- Designed frontend mapping workflows integrating Next.js interface within `/publishers` route.
- Established strict deduplication and metric tracking using canonical domain normalizations.
- Used synthetic datasets for isolated deployment verification of idempotency.

## [Phase 1.9] - 2026-10-09
### Added
- **Workflow Automation Engine**
- Created `Workflow` and `WorkflowRun` models to control automated progression through system stages.
- Added `/workflows` endpoints and Next.js frontend visualization UI.
- Built `WorkflowOrchestrator` to automatically enqueue ARQ tasks according to the configured state machine.
- Updated all intelligence ARQ tasks to trigger the Orchestrator without active polling.
- Fully verified end-to-end execution and transitions on local test databases using Docker Compose.

## [Phase 1.8] - 2026-10-09
### Added
- **Opportunity Intelligence Engine**
- Created `OpportunityProfile` model with `recommended_service`, `opportunity_score`, `supporting_evidence`, `identified_problems`, `confidence_level`, `data_freshness`, `missing_information`, and `recommended_next_action`.
- Created `OpportunityEngine` service to evaluate evidence (WebsiteScan, SEOMetric, AIObservation) and identify opportunities like Technical SEO, Link building, or Content strategy without fabricating data.
- Added `/opportunity/evaluate/{company_id}` and `/opportunity/{company_id}` API routes.
- Integrated `opportunity_evaluation_job` into ARQ workers.
- Added comprehensive `pytest` cases mapping stale data, reproducible scores, missing data, and override conditions.

## [Phase 1.6] - 2026-10-08
### Added
- **AI Extraction & Validation Layer**
- Created base `AIExtractionProvider` and implemented `OpenAIProvider` to query LLMs safely.
- Added strict Pydantic Generics validation `AIEvidence[T]` to enforce taxonomy and schema restrictions directly during LLM deserialization, rejecting hallucinated values automatically.
- Added normalized taxonomies for AI classifications (e.g., `CompanySize`, `CompanyType`, `VerificationStatus`).
- Created 3 new models: `AIExtractionRun` (tracks tokens, models, prompts), `AIObservation` (attribute-level extracted fact tracing), and `AIContradiction` (tracks when an AI contradicts existing verified evidence).
- Ensured evidence-first extraction by enforcing the LLM to provide supporting snippets (`evidence_text`) for every claim.
- Created robust batch testing via Respx mocking.

## [Phase 1.5] - 2026-10-08
### Added
- **SEO Metric Enrichment Engine & Provider Architecture**
- Created base `SEOProvider` interface and generic `ProviderResponse` returning strict typed metric data and API budget usages.
- Added abstract `SEOProviderRegistry` to load, enable, and switch providers uniformly.
- Implemented `AhrefsProvider` (V3 API mapping for `domain_rating`), `MozProvider` (V2 API mapping for `domain_authority`, `spam_score`), and `SemrushProvider` (Domain Overview mapping for `organic_traffic`, `authority_score`).
- Extended `SEOMetric` and `Job` schemas to track detailed batch outputs (`successful_count`, `provider_error_count`, `metrics_skipped`).
- Added `ProviderUsage` model to track explicit estimated API units usage per job.
- Built strict asynchronous isolation in `SEOEnrichmentRunner` (one provider crashing will not wipe out successful peers' results).
- Preserved historical metrics by ensuring every API fetch writes a unique `HistoricalSnapshot` and `Evidence` record along with deterministic `SEOMetric` snapshots.

## [Phase 1.4] - 2026-10-08
### Added
- **Website Intelligence Engine & Crawler Architecture**
- Implemented `CrawlerClient` using `httpx` for deterministic website fetching, redirect tracking, and robots.txt handling.
- Implemented `WebsiteExtractor` using `beautifulsoup4` for HTML metadata extraction (title, description, canonical, h1, etc.), social links extraction, schema.org JSON-LD parsing, and technology detection (Next.js, Cloudflare, React, WordPress).
- Added new Alembic migration `5af30d17b3f1` extending `WebsiteScan` with explicit fields for HTML metadata and technologies.
- Integrated `WebsiteIntelligenceRunner` into the ARQ job queue as `website_analysis_job`.
- Added API routes `POST /analysis/website/{id}`, `GET /analysis/website/{id}`, and `POST /analysis/batch` for scalable crawling.
- Ensured historical scan immutability and provenance tracking in `Evidence` and `SocialProfile`.

## [Phase 1.3] - 2026-10-08
### Added
- **Company Discovery Engine**
- Built scalable modular `Company Discovery Pipeline` connected to `GitHubOrgProvider`.
- Integrated canonical domain normalization, HTTP validation via `HEAD`/`GET` calls, and cross-provider de-duplication using PostgreSQL Integrity constraint safety.
- Handled async generator persistence dynamically and correctly mapped to exact ORM types for ARQ Jobs (`company_discovery_job`).

## [Phase 1.2] - 2026-10-08
### Added
- **Database Foundation + Async Job Infrastructure**
- Created Python 3.12+ environment with FastAPI, SQLAlchemy 2.x, Alembic, and ARQ.
- Created `docker-compose.yml` for PostgreSQL and Redis.
- Implemented SQLAlchemy Models matching `DATA_SCHEMA.md` with UUIDs and JSONB.
- Configured and successfully ran Alembic migrations.
- Built ARQ worker infrastructure (`health_check_job`).
- Built API endpoints (`/health`, `/health/database`, `/health/queue`, `/health/version`, `/jobs`).
- Wrote integration tests using `pytest` and `pytest-asyncio` covering config, database, canonical domain uniqueness, queue, API, and worker logic.

## [Phase 1.1] - 2026-10-08
### Added
- **Project Brain & Data Governance**
- Documentation foundation created (`AGENTS.md`, `MEMORY.md`, `DATA_SCHEMA.md`, `VERIFICATION_RULES.md`).
- Data governance rules established.
- Non-hallucination rules established.
- Evidence model established.
- Historical data requirements established.
- Provider abstraction requirements established.
- Updated `ARCHITECTURE.md` and `DECISIONS.md` to reflect new conceptual architecture and core decisions.
- Added `.env.example`.
