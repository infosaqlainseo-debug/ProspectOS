# ProspectOS Architecture

## Overview
ProspectOS is an AI Agentic Data Intelligence Platform designed to discover companies, analyze their websites, collect verified SEO/domain metrics, discover social profiles, maintain historical records, and prevent hallucinated data.

## Conceptual Architecture Pipeline
`Next.js` &rarr; `FastAPI` &rarr; `ARQ (Redis)` &rarr; `Agent Workers` &rarr; `Crawler / Provider Adapters` &rarr; `Validation` &rarr; `PostgreSQL`

## System Components

### 1. Frontend (Web Dashboard)
- **Role:** User interface for initiating searches, viewing intelligence reports, and managing prospects.
- **Tech Stack (Proposed):** Next.js (React), TailwindCSS, TypeScript.
- **Constraint:** The frontend must never directly access secret provider APIs.

### 2. Backend (API Gateway & Core Services)
- **Role:** Orchestrates requests, manages data storage, and serves data to the frontend.
- **Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy 2.x (asyncpg), Alembic, Pydantic v2.

### 3. Agent Orchestrator & Worker System
- **Role:** Asynchronous job queue managing agentic workflows (web scraping, SEO metrics collection, validation).
- **Tech Stack:** Redis with ARQ for managing long-running background tasks.

### 4. Crawler & Provider Abstraction Layer
- **Role:** Executes web scraping and interacts with external SEO/domain APIs modularly.
- **Components:** `httpx` and `BeautifulSoup4` for deterministic static HTML extraction. Playwright for dynamic page rendering (future).
- **Website Intelligence Engine:** (HTML metadata, Schema, Technologies, Social Links).
  - **SEO Enrichment Engine:** Pluggable adapter interfaces for deterministic querying of Ahrefs, Moz, and Semrush APIs. Handles API budgets, concurrency, rate limits, and provider fault isolation.
  - **AI Extraction & Validation Layer:** Processes unstructured evidence via pluggable LLM providers (e.g. OpenAI) using strictly enforced Pydantic schemas, taxonomy enumerations, and validation checks to prevent hallucinations and maintain historic observations with confidence scoring.
  - **Opportunity Intelligence Engine:** Aggregates facts, metrics, and observations into deterministic `OpportunityProfile`s that identify demand for services (e.g. Link building, Content strategy, Technical SEO) based on explicit evidence tracking and missing data analysis.

### 5. Validation & Evidence Layer
- **Role:** Ensures data adheres to strict non-hallucination schema validations before persistence, ensuring provenance and evidence are recorded for all important facts.
- **AI Intelligence Agents:** Python-based agents interacting with LLMs (e.g., Gemini) for data extraction, reasoning, and rigorous validation.

### 6. Historical Data Layer & Database
- **Role:** Persistent storage preserving observations over time (snapshots) without silently overwriting facts.
- **Components:** PostgreSQL (Source of truth) for relational data (companies, verified metrics, audit logs/history). Redis for ARQ queue state.

## Data Flow
1. User requests a prospect analysis via the Frontend.
2. Backend receives the request, stores initial state in PostgreSQL, and enqueues specific extraction tasks in the ARQ Redis Job Queue.
3. Asynchronous ARQ Workers pick up tasks, triggering Crawler / Provider Adapters to perform external API calls/scraping.
4. Extracted data goes through the Validation & Evidence Layer (utilizing AI agents to structure and verify).
5. Workers save the verified data to the PostgreSQL Database, maintaining an audit trail and historical records.
6. Frontend polls the backend or receives updates via WebSockets to display the completed intelligence report.

### 7. Matching Engine & Media Planning
- **Role:** Transforms ProspectOS from a pure inventory system into a recommendation engine. Matches prospect attributes and campaign constraints against the real publisher inventory.
- **Mechanism:** Given a `CampaignProfile` (Industry, Geography, Budget), the `MatchingEngine` joins `PublisherRecord` and the latest `PublisherObservation`, enforces hard constraints (e.g. Budget > Price), and ranks publishers using a weighted scoring algorithm.
- **Evidence:** Produces `MatchResult`s containing `component_scores`, `reasons`, and `warnings` ensuring explainability for why a publisher was matched or penalized.

### 8. Workflow Orchestration Engine (Phase 2.3)
- **Role:** Coordinates multi-stage pipelines end-to-end with persistent state, progress tracking, fault isolation, and strict human approval boundaries.
- **8-Stage Pipeline:**
  1. `discovery`: Discovers new companies via query or selects designated existing prospects.
  2. `website_analysis`: Crawls website, verifies robots.txt/HTTP status, extracts metadata, technology signals, and social links.
  3. `seo_enrichment`: Enriches domain metrics via pluggable providers (Ahrefs, Moz, Semrush) with usage tracking and failure isolation.
  4. `ai_extraction`: Extracts structured attributes with evidence provenance and contradiction checks.
  5. `opportunity_scoring`: Evaluates deterministic multi-factor opportunity profiles.
  6. `publisher_matching`: Matches prospect profile against real `PublisherRecord` and `PublisherObservation` inventory.
  7. `media_plan_generation`: Auto-assembles top publisher matches into draft `MediaPlan` and `MediaPlanItem` records.
  8. `human_review`: Approval boundary. Halts automatically at `PENDING_APPROVAL`, awaiting explicit human review. Approval transitions `WorkflowRun` to `COMPLETED` and `MediaPlan` to `FINAL`. Rejection marks `REJECTED`.
- **Reliability & Controls:**
  - Idempotency and duplicate-run protection prevent unintended overlapping executions.
  - Per-company failure isolation ensures partial batch success is preserved.
  - Configurable exponential backoff retries (`max_retries`) and provider request limits (`provider_request_limits`).
  - Timezone-aware cron scheduler tick executed via ARQ worker cron (`cron(workflow_scheduler_tick, minute=None, second=0)`).
  - Explicit non-outreach constraint: No cold emails, messaging, or external financial commitments are initiated.

### 9. AI Outreach Automation System (Phase 2.4)
- **Role:** Connects prospect intelligence, SEO opportunities, publisher matching, and media plans to an evidence-driven, human-approved outreach workflow.
- **Components:**
  - **`ContactResearcher`**: Discovers public business contacts from permitted channels (HTML metadata, security.txt, public pages). Assigns verification levels (`VERIFIED` vs `INFERRED`), confidence scores, and retrieval timestamps.
  - **`OutreachPersonalizationEngine`**: Assembles drafts traceable to real database entities (`Company`, `WebsiteScan`, `OpportunityProfile`, `MediaPlan`) with structured `evidence_citations`. Guarantees zero fabricated metrics.
  - **`OutreachSenderService` (9-Stage Barrier)**: Enforces mandatory safety gates prior to any send:
    1. Human Approval Check (`approval_status == 'APPROVED'`)
    2. Draft Un-Sent Check (`status != 'SENT'`)
    3. RFC 5322 Email Syntax Validation
    4. Central Opt-Out & Domain Suppression Check
    5. Contact Record Opt-Out Check
    6. Duplicate Send Prevention (7-day initial outreach cooldown)
    7. Campaign Daily Send Limit Enforcement
    8. Email Provider Readiness Check (`UnconfiguredEmailProvider` safe halt)
    9. Follow-Up Sequence Scheduling (strictly created in `UNAPPROVED` status)
  - **`EmailProviderRegistry`**: Modular provider architecture supporting `MockEmailProvider` (testing), `GmailProvider` (OAuth2), `SMTPProvider` (TLS/STARTTLS), and safe `UnconfiguredEmailProvider` fallback.
  - **Suppression & Sequence Cancellation**: Automatically cancels pending follow-ups upon replies, bounces, or opt-out events. Centralized suppression registry stops future communication across all campaigns.

### 10. CRM & Sales Pipeline System (Phase 2.5)
- **Role:** Connects prospect discovery, SEO intelligence, publisher matching, media plans, workflow automation, and outreach into an observable, measurable sales pipeline.
- **Components:**
  - **11-Stage Configurable Pipeline**: State machine (`NEW`, `RESEARCHED`, `QUALIFIED`, `CONTACTED`, `REPLIED`, `MEETING_SCHEDULED`, `PROPOSAL_SENT`, `NEGOTIATION`, `WON`, `LOST`, `NURTURE`).
  - **Stage Transition Safeguards**:
    - `CONTACTED` requires verified provider-confirmed message delivery or explicit human reviewer action with documented reason; draft generation alone cannot advance stage.
    - `WON` requires explicit authorized human reviewer action; deals and prospects are never won automatically.
  - **Unified 360-Degree Prospect Dossier**: Connects company metadata, website scans (`cms_detected`, `technology_signals`), latest `OpportunityProfile`, associated contacts, media plans, outreach history, deals, tasks, notes, and activity timeline.
  - **Deal & Revenue Management**: Associates deals with companies, contacts, and media plans. Enforces clear separation between estimated open pipeline value and actual earned revenue upon closure (`closed_amount`).
  - **Idempotent Task Engine**: Tracks upcoming and overdue tasks across calls, meetings, research, and follow-ups. Utilizes `idempotency_key` deduplication to prevent duplicate tasks on workflow retries.
  - **Activity Audit Trail**: Immutable chronological log (`CRMActivity`) of stage transitions, deal creations/outcomes, task completions, and internal notes.
  - **Reporting & Conversion Engine**: Computes stage distributions, qualified prospect tallies, win rates, and stage-to-stage conversion rates with transparent data integrity notices.
### 11. AI Sales Intelligence & Lead Prioritization Engine (Phase 3.0)
- **Role:** Evaluates, explains, and prioritizes the strongest SEO and Digital PR sales opportunities among prospects already managed by ProspectOS to focus agency sales efforts on businesses whose observed needs align with GrokxSEO services.
- **Components:**
  - **Granular Opportunity Detection**:
    - Discovers and categorizes deficits across 8 distinct categories: `TECHNICAL_SEO`, `INDEXABILITY_CRAWLABILITY`, `PAGE_METADATA`, `CONTENT_COVERAGE`, `INTERNAL_LINKING`, `BACKLINK_AUTHORITY`, `COMPETITIVE_GAP`, and `DIGITAL_PR_PUBLISHER`.
    - Every opportunity is strictly grounded in verifiable primary records (`WebsiteScan`, `SEOMetric`, `AIObservation`, `PublisherRecord`) with full citation provenance, detection rule, severity, and rationale.
  - **Explainable Multi-Factor Scoring Engine (v3.0.0)**:
    - Computes overall priority score deterministically using configurable weights:
      - SEO Deficit Severity: 35%
      - GrokxSEO Service Fit: 25%
      - Publisher Inventory Alignment: 20%
      - Business & Industry Fit: 10%
      - Evidence Confidence & Freshness: 10%
    - Distinguishes observed technical severity from agency service fit and final sales priority.
    - Transparent handling of missing signals: identifies known limitations and data gaps instead of fabricating metrics or silently defaulting unknowns to zero.
  - **Deterministic Opportunity-to-Service Mapping**:
    - Maps observed findings to 10 GrokxSEO offerings (Technical SEO, SEO Strategy, Content Strategy, Content Architecture, Link Building, Digital PR, Guest Posting, Local SEO, Conversion Optimization, Website Redesign).
    - Recommendations only trigger when supported by evidence (e.g. Digital PR requires niche-aligned vetted publishers from inventory).
  - **Structured Sales Intelligence Briefs**:
    - Generates editable dossiers combining verified company facts, SEO deficit summaries, top opportunities, recommended services with rationale, aligned publishers from inventory, data gaps, discovery questions, and next actions.
    - Supports human customization with version tracking and direct Markdown `.md` export.
  - **Prioritized Sales Queue & Dashboard (`/sales-intelligence`)**:
    - Prioritized queue table ranked by effective score, filterable by industry, service fit, opportunity category, review status, and score thresholds.
    - Side-by-side multi-prospect comparison (2 to 5 prospects).
    - Human override engine with required documentation reason and actor logging to `CRMActivity`.
    - Direct integration with CRM tasks and review status tracking (`UNREVIEWED`, `IN_REVIEW`, `QUALIFIED`, `REJECTED`).

### 12. Publisher Intelligence & Data Quality Monitoring Engine (Phase 3.1)
- **Role:** Ensures continuous, evidence-based quality tracking across all publisher inventory records, detecting missing, stale, invalid, duplicate, and conflicting data while preserving historical observations.
- **Components:**
  - **4-Dimensional Quality Scoring Engine**:
    - Evaluates completeness (25%), validity (25%), freshness (30%), and consistency (20%) yielding scores (0-100) and discrete verdicts (`EXCELLENT`, `ACCEPTABLE`, `POOR`, `CRITICAL`).
  - **Field-Level Independent Freshness Tracking**:
    - Tracks price freshness (stale >30 days), domain metrics freshness (stale >60 days), and website availability (stale >14 days) independently, recording exact check outcomes.
  - **Domain Normalization & Duplicate Detection**:
    - Normalizes URLs to canonical root domains via public suffix recognition, flagging domain collisions across inventory records and mismatches between submitted URLs and company records.
  - **Non-Destructive Observation History & Provenance**:
    - Updates insert new `PublisherObservation` rows tagged as `HUMAN_VERIFIED` or `VERIFIED`, preserving rate-card history without overwriting past observations.
  - **Audited Manual Corrections & Finding Resolution**:
    - Enables attributable corrections with mandatory justification and actor tracking, automatically generating `CRMActivity` audit records.
  - **Safe Provider Refresh Through Authorized Sources**:
    - Interfaces strictly with supported providers (Moz, Ahrefs, internal crawler). Gracefully handles unconfigured API credentials by logging `PROVIDER_NOT_CONFIGURED` without fabricating metrics.
  - **Matching Engine Integration**:
    - Integrates with `MatchingEngine` to flag unverified inventory or observations with stale prices/metrics with explicit warnings in media plan recommendations.
  - **Next.js Quality Dashboard (`/publishers`)**:
    - Interactive overview with KPI cards, directory with quality verdicts, filterable findings table, provider refresh logs, and slide-out inspection drawer with observation timelines and remediation workflows.

### 13. Revenue & Performance Analytics Engine (Phase 3.2)
- **Role:** Delivers persistent, evidence-backed revenue and sales pipeline analytics using the existing CRM database as the single source of truth, enforcing strict financial correctness, non-fabrication of fulfillment costs, and complete separation between realized revenue and open pipeline valuation.
- **Components:**
  - **Realized Revenue vs. Open Pipeline Separation**:
    - Realized revenue is computed strictly from closed deals with `WON` stage/outcome.
    - Open pipeline value accounts strictly for active, non-closed deals. Enriched with stage-probability weights (`DISCOVERY`: 10%, `QUALIFICATION`: 25%, `PROPOSAL`: 50%, `NEGOTIATION`: 75%).
    - Net Realized Revenue formula: `closed_amount - discount_amount + tax_amount - refunded_amount`, preserving granular auditability.
  - **Cost & Profitability Analysis (Zero Fabrication)**:
    - Fulfillment costs are derived strictly from verified `CRMDeal.cost_amount` or itemized `MediaPlanItem.proposed_price`.
    - If cost data is missing, total costs, gross profit, and gross margins are reported as `None`/unavailable rather than zero, preventing false 100% margin calculations. Partial cost coverage is transparently disclosed.
  - **Multi-Currency Normalization Policy**:
    - Preserves un-normalized native currency breakdowns alongside USD-normalized totals.
    - Currency conversion relies on a documented benchmark reference table (`USD: 1.0`, `EUR: 1.08`, `GBP: 1.28`, `CAD: 0.74`, `AUD: 0.66`) with rate sources and timestamps exposed in API metadata.
  - **Sales Funnel & Bottleneck Diagnosis**:
    - Analyzes sequential stage progression (`DISCOVERY -> QUALIFICATION -> PROPOSAL -> NEGOTIATION -> WON`).
    - Calculates stage-to-stage transition conversion rates and drop-off percentages.
    - Automatically diagnoses pipeline bottlenecks, identifying the stage with the lowest progression rate and formulating actionable remedial recommendations.
  - **Correlation-Based Campaign Attribution & ROI**:
    - Attributes deal value to outreach campaigns via direct association while explicitly disclosing that sales-cycle causality is not guaranteed.
    - Enforces a minimum sample threshold ($N \ge 5$) before reporting statistical stability.
  - **Persistent Snapshot Immutability (`RevenueAnalyticsSnapshot`)**:
    - Stores immutable point-in-time snapshots in PostgreSQL table `revenue_analytics_snapshots` for compliance, executive auditing, and periodic trend tracking.
  - **Audited Deals Ledger & Drilldown (`/analytics`)**:
    - Dedicated Next.js dashboard providing executive KPI cards, historical monthly trend tables, sales funnel flow, service and client leaderboards, campaign ROI matrices, and paginated deal drilldowns with complete calculation provenance.

### 14. Advanced Competitive SEO Intelligence Engine (Phase 3.3)
- **Role:** Discovers peer competitors, executes side-by-side crawl and content comparisons, identifies keyword/topical content gaps mapped to search intent, detects technical SEO and internal-linking disparities, handles authorized backlink provider comparisons without metric fabrication, matches Digital PR publisher inventory, and synthesizes prioritized GrokxSEO action plans integrated into the existing sales opportunity engine.
- **Components:**
  - **Competitor Discovery & Relevance Validation**: Discovers candidates directly from PostgreSQL company records using industry categorization, sub-industry alignment, and crawl keyword/heading overlap. Ranks candidates deterministically into `DIRECT`, `INDIRECT`, `TOPICAL_PEER`, and `IRRELEVANT` tiers with explainable evidence.
  - **Side-by-Side Website & Content Benchmark Engine**: Compares word counts, heading hierarchies, SSL security, meta descriptions, XML sitemaps, robots.txt, schema rich snippets, and mobile viewport tags directly from primary `WebsiteScan` records, avoiding simulated data.
  - **Search-Intent & Topical Content Gap Analysis**: Detects competitor keyword advantages and categorizes each gap across four standard search intents (`INFORMATIONAL`, `COMMERCIAL`, `TRANSACTIONAL`, `NAVIGATIONAL`), mapping findings to concrete GrokxSEO content strategy actions.
  - **Technical SEO & Internal Linking Silo Detection**: Identifies technical crawler barriers and compares topical cluster depths and heading hierarchies to pinpoint silo deficits.
  - **Backlink & Authority Differential (Zero Metric Fabrication)**: Compares domain authority and domain rating using authorized SEO provider data (Moz, Ahrefs, Semrush). Where providers are unconfigured or return no data, values remain `None` (Unknown) with explicit disclosures rather than assumed zeros.
  - **Digital PR & Publisher Inventory Matching**: Links competitive PR opportunities directly to real, pre-vetted publisher records (`PublisherRecord` & `PublisherObservation`) matching the target industry, displaying verified rate cards and audience focus.
  - **Deterministic Opportunity Deduplication & Sales Pipeline Sync**: Upserts recommendations into `SalesOpportunity` with deterministic rule keys (`COMPETITIVE_GAP_{domain}_{category}`), preventing duplicate opportunities across modules.
  - **Persistent Models (`CompanyCompetitor`, `CompetitiveAnalysisRun`) & UI (`/competitive-intelligence`)**: Implements dedicated database entities, Alembic migrations, REST API endpoints (`/competitive/...`), and an interactive Next.js dashboard with side-by-side diagnostic tabs and candidate drawers.

### 15. Automated Reporting & Client Portals Engine (Phase 3.4)
- **Role:** Generates branded, client-ready SEO deliverables and hosts secure multi-tenant client workspaces that enforce server-side authentication, role authorization, cross-client isolation, and strict data minimization (protecting internal costs, margins, and sales intelligence), grounded strictly in stored records without metric fabrication.
- **Components:**
  - **Cryptographic Authentication & Role-Based Authorization (`PortalUser`)**:
    - Secures endpoints using salted PBKDF2-HMAC-SHA256 password hashing (100,000 rounds with constant-time verification) and HS256 signed JSON Web Tokens.
    - Enforces three explicit authorization roles: `ADMIN`, `AGENCY_STAFF`, and `CLIENT_USER`.
  - **Server-Side Cross-Client Isolation & Tenancy Boundary**:
    - Enforces tenant isolation in Python services and SQL queries (`enforce_client_isolation`). `CLIENT_USER` accounts are strictly bound to `user.company_id`.
    - Any attempt to access data, reports, or workspaces belonging to another company raises HTTP 403 Forbidden and logs an `UNAUTHORIZED_ACCESS_ATTEMPT` event. Component hiding is never treated as sufficient authorization.
  - **Strict Client-Visible Data Minimization**:
    - Client reports and portals explicitly filter out wholesale publisher costs, agency profit margins, internal CRM notes (`CRMNote`), raw sales lead scores (`SalesIntelligenceScore`), and internal sales stages.
    - Exposes only verified technical website health, client rate deliverables, approved publisher placements, and evidence-backed strategic recommendations.
  - **Evidence-Grounded Report Synthesis (`ClientReport`)**:
    - Synthesizes 7 standard sections (Executive Summary, Technical SEO & Website Health, Content Gaps & Search Intent, Backlink & Authority Verification, Publisher Placements, Campaign Deliverables, Recommendations) from verified primary records (`WebsiteScan`, `OpportunityProfile`, `MediaPlanItem`, `OutreachDraft`).
    - Strictly discloses data limitations and withholds unconfigured third-party metrics in compliance with the ProspectOS Non-Fabrication Policy.
  - **Approval Boundary & Safety Gate**:
    - Reports initialize in `DRAFT` status with `approval_status == 'UNAPPROVED'`.
    - Automated or manual delivery to external recipients strictly requires agency reviewer approval (`approval_status == 'APPROVED'`). Unapproved delivery attempts are rejected with HTTP 400 Bad Request.
  - **Deterministic Idempotency for Duplicate Send Prevention (`ReportDeliveryLog`)**:
    - Generates unique daily idempotency keys (`REPORT_{report_id}_{recipient}_{date}`) preventing duplicate emails during worker retries or repeated user requests.
    - Integrates with the existing email provider registry (`email_registry`), defaulting safely to simulated dispatch when external credentials are absent.
  - **Multi-Format Document Exports**:
    - Generates clean Markdown exports and print-ready HTML exports with client isolation verification and custom agency/client branding.
  - **Automated Scheduling & Background Cadence (`ReportSchedule`)**:
    - Supports recurring generation (`WEEKLY`, `MONTHLY`, `QUARTERLY`) with configurable client time zones and recipient rosters, powered by ARQ background worker tasks (`scheduled_report_generation_job`, `report_delivery_job`).
  - **Persistent Security Audit Logging (`PortalAuditLog`)**:
    - Records immutable audit entries for authentication, report formulation, reviews, approvals, deliveries, invitations, and access attempts.
  - **Next.js Dashboard Integration (`/reports`, `/portal`)**:
    - Agency Reports Manager at `/reports`: Generation wizard, approval workflow, cadence scheduler, export viewer, and audit trail drawer.
    - Client Workspace Portal at `/portal`: Client-sanitized portal displaying crawl health, strategic deliverables, approved placements, certified deliverables library, and team invitation management.

