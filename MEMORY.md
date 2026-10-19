# ProspectOS Memory

*Operational Project Memory. DO NOT store company databases here.*

## Current Project State
- **Phase:** 3.4 — Automated Reporting & Client Portals
- **Status:** Fully implemented and validated. The Automated Reporting & Client Portals system delivers secure multi-tenant client portals and evidence-backed deliverable formulation. Features include PBKDF2-HMAC-SHA256 password hashing with signed JWT session authentication across three roles (`ADMIN`, `AGENCY_STAFF`, `CLIENT_USER`), server-side cross-tenant isolation (`enforce_client_isolation`) rejecting unauthorized access with 403 Forbidden and logging audit events, strict client data minimization (excluding internal agency profit margins, wholesale publisher costs, raw lead priority scores, and internal notes), evidence-grounded report synthesis from stored records (`WebsiteScan`, `OpportunityProfile`, `MediaPlanItem`, `OutreachDraft`), strict non-fabrication disclosure caveats for unconfigured third-party providers, mandatory agency approval boundary before external report delivery (`approval_status == 'APPROVED'`), deterministic idempotency keys (`REPORT_{report_id}_{recipient}_{date}`) preventing duplicate email dispatches during job retries, Markdown and print-ready HTML exports, background cadence scheduling (`ReportSchedule`) across time zones, immutable audit logs (`portal_audit_logs`), full REST API at `/portal`, and Next.js dashboards at `/reports` (agency manager) and `/portal` (client workspace).

## Current Architecture
- **Frontend:** Next.js (React 19 / Next 16 Turbopack, TailwindCSS v4, TypeScript)
- **Backend:** Python 3.12+ (FastAPI, SQLAlchemy 2.x, Alembic, asyncpg)
- **Database:** PostgreSQL (Source of truth, running in Docker)
- **Job Queue:** ARQ (Async Redis Queue) + Redis (running in Docker)
- **Data Governance:** Strict evidence-first, non-hallucination validation pipelines with API usage tracking. Field-level freshness tracking and non-destructive historical observations. Strict human approval boundary enforced before any email transmission. Immutable CRM activity audit trail. Transparent explainability without metric fabrication. Strict financial correctness and separation between realized revenue and unearned pipeline. Server-side multi-tenant isolation and strict data minimization for client-facing workspaces.

## Completed Modules
- Phase 1.1: Project Brain, Memory & Data Governance Documentation
- Phase 1.2: Database Foundation + Async Job Infrastructure
- Phase 1.3: Company Discovery Engine (GitHub Organizations)
- Phase 1.4: Website Intelligence Engine
- Phase 1.5: SEO Metric Enrichment Engine
- Phase 1.6: AI Extraction & Validation Layer
- Phase 1.7: Next.js Dashboard (partial structure)
- Phase 1.8: Prospect Opportunity Intelligence Engine
- Phase 1.9: Workflow Automation Engine (initial scaffold)
- Phase 2.0: Publisher Inventory Integration (Import pipelines, observations tracking, Next.js importer UI)
- Phase 2.1: Intelligent Publisher Matching & Explainable Ranking (Campaign profiles, Scoring engine, Constraints, Evidence-driven matching UI)
- Phase 2.2: Media Plan Builder & Shortlist Management
- Phase 2.3: Workflow Automation Engine (8-stage persistent orchestrator, live UI controls, retries/isolation, scheduler, human approval boundary)
- Phase 2.4: AI Outreach Automation (Contact provenance, evidence citations, 9-stage sending barrier, human approval gate, modular providers, opt-out suppression, follow-up cancellation, Next.js outreach dashboard)
- Phase 2.5: CRM & Sales Pipeline (Configurable 11-stage pipeline, transition safeguards, unified prospect records, deal revenue tracking, idempotent task engine, internal notes, activity timeline, Next.js Kanban & CRM dashboard)
- Phase 3.0: AI Sales Intelligence & Lead Prioritization (8-category opportunity detection, explainable scoring v3.0.0, service-to-opportunity mapping, editable sales briefs with Markdown export, side-by-side comparison, human override auditing, prioritized sales queue dashboard)
- Phase 3.1: Publisher Intelligence & Data Quality Monitoring (Persistent quality scoring, domain validation, duplicate detection, field-level freshness, historical observation preservation, audited manual corrections, safe finding resolutions, approved provider refresh, matching engine quality warnings, Next.js quality dashboard)
- Phase 3.2: Revenue & Performance Analytics (Realized won revenue, separated open pipeline, weighted pipeline, fulfillment costs & gross profit without fabrication, multi-currency benchmark normalization, funnel conversion rates & bottleneck detection, correlation-based campaign ROI, persistent snapshots, deals ledger drilldown, Next.js revenue analytics dashboard)
- Phase 3.3: Advanced Competitive SEO Intelligence (Competitor discovery, side-by-side crawl comparison, search-intent content gaps, technical/silo disparities, non-fabricated backlink authority comparison, publisher inventory matching, GrokxSEO recommendation priority scoring, deterministic opportunity deduplication, Next.js competitive dashboard)
- Phase 3.4: Automated Reporting & Client Portals (Role-based authentication, server-side tenant isolation, client data minimization, evidence-backed report synthesis, strict non-fabrication disclosures, approval boundary delivery gate, idempotent send prevention, multi-format exports, cadence scheduling, audit logging, Next.js `/reports` and `/portal` dashboards)

## Pending Modules
- Phase 3.5+: Additional Advanced Enhancements (Strictly requires separate explicit user authorization)

## Important Implementation Decisions
- Python 3.12+ and async workflows across the board (FastAPI + asyncpg + ARQ).
- PostgreSQL is the persistent source of truth.
- The LLM is not the source of truth for factual metrics.
- Evidence/provenance is mandatory for important external facts.
- Historical observations are preserved (never silently destroyed).
- Provider integrations must be modular.
- Crawler and enrichment jobs must be asynchronous.

## Known Limitations & Technical Risks
- External scraping and APIs are inherently unreliable/slow. The system must gracefully handle failures without destroying jobs.
- Differing SEO metrics (e.g., DA vs. DR) must not be conflated.
- LLM outputs require strict schema validation to prevent hallucinations.

## Known Provider Requirements
- SEO API Keys (Moz, Ahrefs, Semrush, Majestic, Similarweb).
- LLM API Keys (Gemini/OpenAI) for extraction and reasoning.

## Future Work (Beyond Phase 1)
- Automated cold email, spam prevention mechanisms, client outreach, marketplace matching, automated sales, CRM automation.
