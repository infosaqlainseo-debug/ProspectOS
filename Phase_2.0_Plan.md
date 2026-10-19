# Phase 2.0 Implementation Plan: Publisher Inventory Integration

## 1. Inspection Findings
I have comprehensively inspected the existing architecture, database models (`DATA_SCHEMA.md` and `app/models/__init__.py`), and workspace directory.

**Missing Source Inventory**: I have scanned the repository and found **no real publisher inventory source files** (no `.csv`, `.xlsx`, or `.xls` files) nor any database dump. Therefore, I will build the robust import pipeline and UI, test it with a clearly labelled synthetic fixture, and **request the real source file from you** before a production import.

**Existing Schema & Integration Points**: 
The existing `Company` and `Domain` models provide an excellent foundation (canonical domains, deduplication). Rather than creating a completely redundant `Publisher` table that replicates canonical domain tracking, I will extend the schema relationally to preserve normalization.

## 2. Planned Schema Updates

I will implement the following models in a new Alembic migration:

1. **`PublisherRecord` (Table: `publisher_records`)**:
   - `id`: Internal stable UUID.
   - `company_id`: FK to `companies` (1:1 relation), anchoring it to the canonical domain.
   - `original_submitted_url`: Preserves raw input.
   - `audience_focus`, `editorial_attributes`: New specific publisher metadata fields.
   - `status`: Verification status.

2. **`PublisherObservation` (Table: `publisher_observations`)**:
   - `id`, `publisher_id`
   - `price`, `currency`, `pricing_model`
   - `metric_da`, `metric_dr`, `metric_traffic` (recorded *only* when imported from the source)
   - `observation_timestamp`, `source_name`
   - **Note:** Real historical snapshotting - new imports will insert new observations rather than overwriting old pricing.

3. **`ImportBatch` & `ImportAuditRow` (Tables: `import_batches`, `import_audit_rows`)**:
   - For complete provenance: tracks file names, success counts, row-level validation errors, skipped duplicates, and timestamps.

## 3. Import Pipeline Architecture

The pipeline will be built in `backend/app/services/import_pipeline.py`:
- **Step 1: Upload**: `POST /api/publishers/import/upload` to parse CSV (using `pandas` or `csv`).
- **Step 2: Column Mapping & Preview**: Returns detected headers and first 5 rows to UI.
- **Step 3: Validation**: Uses Pydantic to validate currencies, URLs, and numeric metrics. NULLs will be preserved.
- **Step 4: Normalization & Duplicate Detection**: Matches canonical domains against the existing `Company` table.
- **Step 5: Commit**: `POST /api/publishers/import/commit` executes idempotently within a transaction, preserving original metrics.

## 4. Next.js Dashboard Updates
- **`/publishers`**: A new data table view for verified/unverified publishers.
- **`/publishers/import`**: A stepper UI (Upload -> Map Columns -> Preview/Conflicts -> Summary).

## 5. Risks & Limitations
- Duplicate resolution logic will default to "Skip/Flag" if identities are ambiguous.
- Excel support will require installing `openpyxl`.

I will now proceed with implementing the database models and the backend import pipeline. I will test it with a synthetic CSV fixture first. Please provide the real inventory file when ready!
