# Phase 2.1 Gap Analysis and Implementation Plan

## 1. Audit of Current State
- **Current Inventory**: ProspectOS has a solid foundation of canonical `Company` records linked to `PublisherRecord` and `PublisherObservation` entries representing the actual inventory with pricing and DA/DR/Traffic metrics.
- **Current Intelligence**: Existing architecture supports `WebsiteScan`, `SEOMetric`, and `AIObservation` which provide industry, summary, and intent data for prospect companies.
- **Gap**: We lack the connective tissue (matching logic, scoring algorithm) and the persistence layer (campaign profiles, matching runs, results, shortlists) to intelligently route a prospect to the most relevant publishers.

## 2. New Database Models
To support Phase 2.1 without duplicating existing data or compromising the inventory:
- `CampaignProfile`: Stores the compiled profile (industry, topics, audience, geography, budget) for a prospect. Allows the user to edit/review before matching.
- `MatchingRun`: Records a specific execution of the matching engine. Contains the `profile_snapshot` used, `scoring_model_version`, `status`, and timestamps.
- `MatchResult`: Stores individual publisher scores generated during a `MatchingRun`. Includes `overall_score`, `component_scores` (JSONB), `reasons` (JSONB), and `evidence` (JSONB).
- `Shortlist` and `ShortlistItem`: Represents curated lists of publishers derived from matching runs or manual selection, enabling media plan generation.

## 3. Matching Engine Logic
- **Profile Assembly**: The engine will pre-fill a `CampaignProfile` using the prospect's `Company`, `AIObservation` (for industry/audience), and `SEOMetric` data.
- **Scoring Model (v1.0)**:
  - *Topical & Semantic Relevance (35%)*: Match prospect's industry/topics against publisher's category/topics.
  - *Audience & Industry Alignment (20%)*: Match B2B/B2C focus.
  - *Geographic Relevance (10%)*: Compare prospect's target geo with publisher's origin/audience.
  - *Publisher Quality (15%)*: DA/DR metrics normalized.
  - *Price & Budget (10%)*: Publisher price vs campaign max budget.
  - *Editorial Suitability (10%)*: Content format compatibility.
- **Hard Exclusions**: If a publisher's price exceeds a strict budget, or if mandatory geo constraints fail, the publisher is excluded.
- **Evidence generation**: Every component score will include a human-readable reason (e.g., "Industry 'Technology' matches publisher category 'Software'").

## 4. API Endpoints
- `GET /campaigns/prospect/{company_id}/profile`: Auto-assemble or retrieve a saved prospect matching profile.
- `PUT /campaigns/prospect/{company_id}/profile`: Save/update the campaign profile.
- `POST /matching/run`: Trigger an async (or sync if fast enough) matching run for a profile.
- `GET /matching/runs/{run_id}`: Retrieve matching run status and summary.
- `GET /matching/runs/{run_id}/results`: Retrieve ranked publishers with explanations.
- `POST /shortlists`: Create a shortlist.
- `POST /shortlists/{id}/items`: Add publishers to a shortlist.
- `GET /shortlists/{id}/export`: Export media plan (CSV/XLSX).

## 5. Frontend Updates
- Add a new "Media Planning" or "Matching" tab on the prospect detail page.
- Workflow steps:
  1. Profile Review (form prepopulated with AI data).
  2. Matching Run triggers loading state.
  3. Results view with scores, breakdowns, and warnings (missing data).
  4. Selection tool to add to Shortlist.
  5. Shortlist view with Budget aggregation and Export button.

## 6. Execution Order
1. Generate Alembic migrations for new models (`CampaignProfile`, `MatchingRun`, `MatchResult`, `Shortlist`, `ShortlistItem`).
2. Implement `MatchingEngine` service in `backend/app/services/matching/engine.py`.
3. Create API routes in `backend/app/api/matching.py` and `backend/app/api/campaigns.py`.
4. Update frontend components.
5. Write and execute tests (`tests/test_matching.py`).
6. Perform controlled real-data validation and update project memory.
