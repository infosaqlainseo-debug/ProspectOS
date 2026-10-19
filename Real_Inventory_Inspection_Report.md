# Real Publisher Inventory Inspection & Import Preview

## 1. Source Validation
- **Status:** **VERIFIED**
- **Source URL:** `https://docs.google.com/spreadsheets/d/e/2PACX-1vRBhEEZJicy0bmuNC1EKvalm71ohBS8Q6pTaEJ_yp4bemVGG63Qrf9o2zY7zWaa4Q/pub?output=xlsx`
- **Downloaded Location:** `backend/data/imports/real_inventory.xlsx`
- **File Format:** Valid Excel Workbook (`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`)
- **File Size:** ~134 KB
- **Modification:** The source file remains **unchanged**. We have exclusively performed a non-destructive read via `pandas`.

## 2. Worksheet Inspection
- **Total Rows:** 1912
- **Columns Identified:** 9 (`['Website/Publication Name', 'URL', 'Price', 'DA', 'DR', 'TAT', 'Region', 'Sponsored', 'Do follow']`)

**Representative Sample (First Row):**
- **Name:** Medium
- **URL:** `medium.com`
- **Price:** $17.25
- **DA:** 95.0
- **DR:** 94.0

## 3. Data Integrity & Schema Mapping
The Excel columns have been seamlessly mapped to the ProspectOS backend API:
- `url_column` → `URL`
- `publisher_name_column` → `Website/Publication Name`
- `price_column` → `Price`
- `da_column` → `DA`
- `dr_column` → `DR`

### **Anomalies Discovered:**
- **Missing/Invalid URLs:** 241 rows contain `"Not Available"` in the URL column. 4 rows have an empty or fundamentally malformed URL. 
  - *Fix Applied:* I updated the `normalize_domain` logic in the backend to explicitly reject empty suffixes and `"Not Available"` strings, correctly registering these as `FAILED` audit rows rather than erroneously merging them all into a `"not available."` canonical company.
- **Duplicate Domains:** Out of the 1912 rows, there are over 250 duplicate canonical domains (e.g., multiple entries for `usatoday.com`, `digitaltrends.com`). The backend correctly processes these via an idempotent UPSERT, preserving the existing record while appending a new historical `PublisherObservation`.

## 4. Import Preview (Dry-Run)
We successfully piped the cleaned dataset through the `commit_import` API using a new `dry_run=True` transaction rollback parameter to prevent any database pollution.

**Proposed Import Counts:**
- **Total Rows Scanned:** 1912
- **Valid Rows Accepted:** 1667
- **New Publishers Created:** 1413
- **Existing Publishers Updated:** 254 *(Duplicates inherently resolved and appended as historical observations)*
- **Invalid/Rejected Rows:** 245 *(Missing or 'Not Available' URLs)*
- **Skipped Rows:** 0

## 5. Next Action
The actual database is entirely unmodified, and all data preservation rules are strictly upheld. **Do you approve the execution of the final commit to insert these 1413 publishers into the live database?** 
*(Once approved, we will drop the `dry_run=True` flag and execute the migration permanently.)*
