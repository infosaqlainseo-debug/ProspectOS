# ProspectOS — Crawler Resilience and Evidence Fallback Remediation Report

**Date:** October 14, 2026  
**System:** ProspectOS Platform  
**Target:** Safe Crawler Failure Handling, Evidence Fallback, and Score Calibration  
**Verdict:** **PASS WITH ISSUES** (Remediation Passed; Bot-Protection Access Restrictions Accurately Preserved)

---

## 1. Executive Summary

Following the Controlled Operational Pilot V2 review, a targeted remediation task was executed to address bot-protected domains that returned HTTP 403. 

Previously, automated HTTP 403 responses returned from Cloudflare WAF challenge pages were mistakenly processed as completed crawls. As a consequence, challenge HTML strings (such as `<title>Just a moment...</title>`) were passed into downstream DOM extractors. This produced false on-page defect signals (e.g., "Under-Optimized Short Title Tag", "Missing Primary H1 Heading Tag", "Missing Meta Description Tag"), which artificially inflated technical SEO opportunity counts and lead qualification scores to 80.5–83.0.

### Remediation Outcomes:
1. **Accurate Failure Classification:** HTTP 403 responses are now explicitly recorded as `ACCESS_RESTRICTED` with `is_accessible: False` and classified with human-readable diagnostic reasons (`BOT_PROTECTION_CHALLENGE (Cloudflare WAF / Bot Management)`). Non-200 responses return empty HTML (`html: ""`), preventing challenge text from ever polluting extractors.
2. **Strict Non-Evasion Policy:** No stealth headers, CAPTCHA solving, proxy rotation, or bot impersonation techniques were introduced. Standard robots.txt directives and provider rate limits remain respected. Single-attempt fail-fast behavior eliminates aggressive retries on blocked endpoints.
3. **Authorized Fallback & Provenance:** When direct crawling is restricted, the platform queries permitted fallback sources (recent historical scans `<30 days`, verified publisher catalog matches, authorized company registry data) and explicitly registers unavailable on-page attributes as `UNAVAILABLE` with status `UNVERIFIED` in the `Evidence` table.
4. **Scoring Calibration & Downstream Integrity:** False on-page opportunities are completely suppressed for restricted crawls. Only a single advisory `INDEXABILITY_CRAWLABILITY` opportunity (Severity: `MEDIUM`) is created. Lead priority scores for the affected domains recalibrated from inflated levels (~81–83) down to an explainable baseline (~60.8), with primary service recommendations shifting to `DIGITAL_PR` (grounded in verified inventory matches).
5. **Validation:** 100 out of 100 tests pass, including 6 dedicated crawler resilience and score calibration unit/regression tests. Live reruns of the 3 affected prospects completed with 100% data integrity.

---

## 2. Affected Prospect Records & Root Cause Diagnostics

| Prospect Domain | Company ID | HTTP Status | Response Server | Cloudflare Ray ID | Diagnostic Root Cause |
|---|---|---|---|---|---|
| `thedefiant.io` | `fb123d33-8f6a-4ff5-8c36-3b5b29fd157b` | 403 Forbidden | `cloudflare` | `98e3b745ca1684c3` | Cloudflare Managed Bot Challenge / WAF challenge page (`<title>Just a moment...</title>`) |
| `healthcarebusinesstoday.com` | `d4730d76-4201-4c35-aa69-edda432d640b` | 403 Forbidden | `cloudflare` | `98e3b7625dc984c3` | Cloudflare WAF Challenge / Rate-Protection Block (`<title>Attention Required! \| Cloudflare</title>`) |
| `australianaviation.com.au` | `3af064e3-f1c8-438a-b5ce-a714ee293bff` | 403 Forbidden | `cloudflare` | `98e3b77dcbf684c3` | Cloudflare Managed Challenge / Regional Bot Filtering |

### Detailed Findings:
- **Robots.txt Analysis:** Each domain's `robots.txt` was fetched and parsed. For example, `thedefiant.io` serves `User-agent: * Allow: /`. The restriction is not an explicit robots.txt disallow rule, but an edge WAF challenge configured to challenge non-browser automated HTTP clients (User-Agent: `ProspectOS-Crawler/1.0`).
- **Defect in Prior Implementation:** The previous crawler did not check `is_accessible` before extracting metadata, and failed to differentiate between a successful page fetch and a challenge response. As a result, the crawler extracted `<title>Just a moment...</title>` (16 characters), generating an erroneous "Under-Optimized Short Title Tag (16 chars)" opportunity.

---

## 3. Code Modifications & Relevant Files

The following files were surgically updated without altering unrelated features or external integrations:

### 1. `backend/app/services/crawler/client.py`
- Enhanced `fetch_page()` to inspect status codes and server headers.
- On HTTP 403: Detects `cloudflare` server or `cf-ray` header and records `failure_reason = "BOT_PROTECTION_CHALLENGE (Cloudflare WAF / Bot Management)"`.
- Differentiates 401 (`AUTHENTICATION_REQUIRED`), 429 (`RATE_LIMIT_EXCEEDED`), 5xx (`SERVER_ERROR`).
- Sets `is_accessible = False` and `status = "ACCESS_RESTRICTED"`.
- Sets `html = ""` for any non-200 response to ensure zero challenge DOM leakage.
- Enforces single-request termination on 403/401 to prevent aggressive retries.
- Integrated `urllib.robotparser.RobotFileParser` in `fetch_robots_txt()`.

### 2. `backend/app/services/intelligence/runner.py`
- On `not is_accessible`:
  - Sets `scan.title = None`, `meta_description = None`, `canonical_url = None`, `h1 = None`, `h2 = None`, `schema_detected = None`.
  - Records diagnostic metadata in `scan.technology_signals` (`is_accessible: False`, `failure_reason`, `status_code`, `server`).
  - Sets `scan.scan_status = "ACCESS_RESTRICTED"`.
  - Executes permitted fallback collection:
    - **Fallback A (Historical Archive):** Collects prior verified scans (`< 30 days`) and records `Evidence` with status `VERIFIED_HISTORICAL`.
    - **Fallback B (Authorized Catalog Feed):** Preserves verified company name and publisher records with status `VERIFIED` and provider `authorized_catalog_inventory`.
    - **Fallback C (Unverified On-Page Logging):** Explicitly records `field_name="on_page_seo_content"`, `value="UNAVAILABLE"`, `verification_status="UNVERIFIED"`, `confidence=0.0`.

### 3. `backend/app/services/ai/runner.py`
- In `_gather_evidence_text()`:
  - Detects if `scan.http_status == 403` or `scan_status == "ACCESS_RESTRICTED"`.
  - Pulls verified fallback evidence from `Evidence` table.
  - Appends anti-hallucination instruction: `"CRITICAL INSTRUCTION: Live on-page HTML is blocked by bot protection. Only extract verifiable company attributes from the fallback evidence above. Do NOT invent page titles, headings, or on-page SEO findings. Mark unverified on-page attributes as UNVERIFIED."`

### 4. `backend/app/services/intelligence/opportunity.py`
- In `OpportunityEngine.evaluate_company()`:
  - Checks `is_blocked = (latest_scan.http_status == 403 or latest_scan.scan_status == "ACCESS_RESTRICTED")`.
  - When `is_blocked`: Emits a single problem (`Automated crawler blocked by bot protection (HTTP 403)`), adds missing on-page data to `missing_information`, and prevents false "Missing H1 tags" or robots.txt issues.
  - Sets moderate baseline score (`55.0`) instead of inflating to 90–100.
  - Caps confidence level at `0.70` (or `0.40` if no observations).

### 5. `backend/app/services/intelligence/sales_intelligence.py`
- In `detect_opportunities()`:
  - On HTTP 403 / `is_blocked`: Emits a single `INDEXABILITY_CRAWLABILITY` opportunity with `severity="MEDIUM"` (title: `"Automated Crawler Blocked by Bot Protection (HTTP 403)"`).
  - Gates all on-page checks (`PAGE_METADATA`, `CONTENT_ARCHITECTURE`, `CONTENT_COVERAGE`) to only evaluate when the crawl is unblocked.
- In `calculate_service_fits()`:
  - Prevents artificial 80.0 boost to `TECHNICAL_SEO` when the non-200 code is an edge bot challenge (HTTP 403).
- In `calculate_priority_score()`:
  - Adjusts data completeness calculation (awards 0.5 for blocked scan reachability, reflecting unverified content).
  - Explicitly appends `"Direct website crawling blocked by bot protection (HTTP 403 / Cloudflare WAF)"` to `limitations`.
  - Appends `"Direct on-page SEO signals (H1, title length, meta description, body copy) unverified"` to `missing_information`.

---

## 4. Test Suite Execution & Verification

### A. Dedicated Crawler Resilience Test Suite (`backend/tests/test_crawler_resilience.py`)
A comprehensive suite of 6 automated tests was implemented and executed:

| Test Name | Focus | Outcome |
|---|---|---|
| `test_crawler_classifies_cloudflare_bot_challenge` | Verifies Cloudflare headers, 403 classification, empty HTML, and no retries | **PASS** |
| `test_crawler_classifies_http_failure_status_codes` | Validates classification of 401, 429, and 500 status codes | **PASS** |
| `test_runner_preserves_clean_scan_and_records_fallback_evidence` | Verifies fallback records, provenance, and `UNAVAILABLE`/`UNVERIFIED` evidence | **PASS** |
| `test_opportunity_engine_does_not_fabricate_issues_on_403` | Verifies no false H1 tags and calibrated baseline score (55.0) | **PASS** |
| `test_sales_intelligence_single_advisory_opportunity_on_403` | Confirms single MEDIUM opportunity, calibrated score, and DIGITAL_PR priority | **PASS** |
| `test_ai_runner_gather_evidence_anti_hallucination` | Verifies anti-hallucination guard and fallback inclusion in LLM prompt | **PASS** |

### B. Full Backend Regression Run
Execution of all 100 backend test cases:
```
backend/tests/test_ai_extraction.py ..                                   [  2%]
backend/tests/test_anthropic_extraction.py ...........                   [ 13%]
backend/tests/test_client_portal_and_reporting.py ..........             [ 23%]
backend/tests/test_competitive_intelligence.py ....                      [ 27%]
backend/tests/test_crawler_resilience.py ......                          [ 33%]
backend/tests/test_crm.py ......                                         [ 39%]
backend/tests/test_main.py ....                                          [ 43%]
backend/tests/test_matching.py .                                         [ 44%]
backend/tests/test_media_plan.py .                                       [ 45%]
backend/tests/test_opportunity_engine.py .....                           [ 50%]
backend/tests/test_outreach.py .........                                 [ 59%]
backend/tests/test_pipeline.py .                                         [ 60%]
backend/tests/test_providers.py .....                                    [ 65%]
backend/tests/test_publisher_quality.py .........                        [ 74%]
backend/tests/test_publishers.py ..                                      [ 76%]
backend/tests/test_revenue_analytics.py ........                         [ 84%]
backend/tests/test_sales_intelligence.py ......                          [ 90%]
backend/tests/test_url.py ..                                             [ 92%]
backend/tests/test_workflow_orchestrator.py ........                     [100%]

============================= 100 passed in 13.94s =============================
```

---

## 5. Before-and-After Analysis for Affected Prospects

A live workflow rerun was executed across all three affected prospects. Live Ahrefs Domain Rating (DR) metrics and existing publisher records were preserved without repeating unnecessary paid API requests.

### Prospect 1: `thedefiant.io`
- **Prospect ID:** `fb123d33-8f6a-4ff5-8c36-3b5b29fd157b`
- **Domain Authority:** DR 73.0 (Ahrefs v3 verified)
- **Publisher Matches:** 5 matching publishers (Cryptocurrency & DeFi vertical)

| Dimension | Pilot V2 (Before Remediation) | Remediation Rerun (Current) | Variance / Delta |
|---|---|---|---|
| **Crawl Status** | `COMPLETED` *(False Positive)* | `ACCESS_RESTRICTED` *(Accurate)* | Corrected |
| **HTTP Status Code** | 403 | 403 | Preserved |
| **Failure Classification** | None recorded | `BOT_PROTECTION_CHALLENGE (Cloudflare WAF / Bot Management)` | Added |
| **Extracted Page Title** | `"Just a moment..."` *(Fabricated from challenge)* | `None` | Challenge text eliminated |
| **Extracted H1** | `[]` (Marked as Missing H1) | `None` (Marked as Unverified) | Fixed |
| **Detected Opportunities** | 5 (HTTP 403, Short Title, Missing Meta, Missing H1, Publisher Match) | 2 (Bot Challenge, Publisher Match) | 3 false opportunities eliminated |
| **SEO Severity Score** | 80.0 / 100.0 *(Artificially High)* | 30.0 / 100.0 | -50.0 points |
| **Overall Priority Score** | **83.0** *(Critical Priority)* | **60.8** *(Moderate / Verified)* | -22.2 points (Calibrated) |
| **Primary Service Rec** | `TECHNICAL_SEO` *(False Claim)* | `DIGITAL_PR` *(Publisher Grounded)* | Aligned to verified evidence |
| **Data Completeness** | 0.75 | 0.62 | Reflected unverified on-page |
| **Evidence Provenance** | None for crawl block | Fallback records logged (`AUTHORIZED_CATALOG_FEED`, `RESTRICTED_CRAWL: UNAVAILABLE`) | Provenance established |

---

### Prospect 2: `healthcarebusinesstoday.com`
- **Prospect ID:** `d4730d76-4201-4c35-aa69-edda432d640b`
- **Domain Authority:** DR 63.0 (Ahrefs v3 verified)
- **Publisher Matches:** 5 matching publishers (Healthcare & Healthtech vertical)

| Dimension | Pilot V2 (Before Remediation) | Remediation Rerun (Current) | Variance / Delta |
|---|---|---|---|
| **Crawl Status** | `COMPLETED` *(False Positive)* | `ACCESS_RESTRICTED` *(Accurate)* | Corrected |
| **HTTP Status Code** | 403 | 403 | Preserved |
| **Failure Classification** | None recorded | `BOT_PROTECTION_CHALLENGE (Cloudflare WAF / Bot Management)` | Added |
| **Extracted Page Title** | `"Attention Required! \| Cloudflare"` *(Fabricated)* | `None` | Challenge text eliminated |
| **Extracted H1** | `[]` (Marked as Missing H1) | `None` (Marked as Unverified) | Fixed |
| **Detected Opportunities** | 5 (HTTP 403, Short Title, Missing Meta, Missing H1, Publisher Match) | 2 (Bot Challenge, Publisher Match) | 3 false opportunities eliminated |
| **SEO Severity Score** | 80.0 / 100.0 | 30.0 / 100.0 | -50.0 points |
| **Overall Priority Score** | **80.5** *(Critical Priority)* | **60.8** *(Moderate / Verified)* | -19.7 points (Calibrated) |
| **Primary Service Rec** | `TECHNICAL_SEO` *(False Claim)* | `DIGITAL_PR` *(Publisher Grounded)* | Aligned to verified evidence |
| **Data Completeness** | 0.75 | 0.62 | Reflected unverified on-page |
| **Evidence Provenance** | None for crawl block | Fallback records logged (`AUTHORIZED_CATALOG_FEED`, `RESTRICTED_CRAWL: UNAVAILABLE`) | Provenance established |

---

### Prospect 3: `australianaviation.com.au`
- **Prospect ID:** `3af064e3-f1c8-438a-b5ce-a714ee293bff`
- **Domain Authority:** DR 65.0 (Ahrefs v3 verified)
- **Publisher Matches:** 5 matching publishers (Aviation, Defense & Transport vertical)

| Dimension | Pilot V2 (Before Remediation) | Remediation Rerun (Current) | Variance / Delta |
|---|---|---|---|
| **Crawl Status** | `COMPLETED` *(False Positive)* | `ACCESS_RESTRICTED` *(Accurate)* | Corrected |
| **HTTP Status Code** | 403 | 403 | Preserved |
| **Failure Classification** | None recorded | `BOT_PROTECTION_CHALLENGE (Cloudflare WAF / Bot Management)` | Added |
| **Extracted Page Title** | `"Attention Required! \| Cloudflare"` *(Fabricated)* | `None` | Challenge text eliminated |
| **Extracted H1** | `[]` (Marked as Missing H1) | `None` (Marked as Unverified) | Fixed |
| **Detected Opportunities** | 5 (HTTP 403, Short Title, Missing Meta, Missing H1, Publisher Match) | 2 (Bot Challenge, Publisher Match) | 3 false opportunities eliminated |
| **SEO Severity Score** | 80.0 / 100.0 | 30.0 / 100.0 | -50.0 points |
| **Overall Priority Score** | **80.5** *(Critical Priority)* | **60.8** *(Moderate / Verified)* | -19.7 points (Calibrated) |
| **Primary Service Rec** | `TECHNICAL_SEO` *(False Claim)* | `DIGITAL_PR` *(Publisher Grounded)* | Aligned to verified evidence |
| **Data Completeness** | 0.75 | 0.62 | Reflected unverified on-page |
| **Evidence Provenance** | None for crawl block | Fallback records logged (`AUTHORIZED_CATALOG_FEED`, `RESTRICTED_CRAWL: UNAVAILABLE`) | Provenance established |

---

## 6. Downstream Data Quality & Policy Compliance Audit

1. **No Cold Outreach or Automated Messaging:** `EMAIL_PROVIDER="none"` remains hard-coded and strictly enforced. No email dispatch occurred.
2. **No Evasion or Circumvention:** No browser fingerprints were spoofed, no rotating residential proxies were deployed, and no CAPTCHA solvers were utilized.
3. **Traceability and Data Lineage:** Every fallback attribute in `Evidence` includes explicit `source_type` (`AUTHORIZED_CATALOG_FEED`, `RESTRICTED_CRAWL`), `provider`, `confidence`, and `verification_status`.
4. **No Metric Contamination:** Third-party Ahrefs DR metrics (DR 63–74) are never used as a proxy for missing website titles, headings, or on-page copy. Missing on-page fields remain `None` and are labeled `UNVERIFIED`.
5. **Explainability in Sales Briefs:** Regenerated sales briefs for all three prospects explicitly highlight data gaps:
   - Gap 1: `"Direct on-page SEO signals (H1, title length, meta description, body copy) unverified"`
   - Gap 2: `"AI Qualitative Observations (content quality, value proposition)"`
   - Next Action: Direct sales conversations are guided toward publisher placements (`DIGITAL_PR`) rather than unsubstantiated claims of broken title tags or missing headings.

---

## 7. Remaining Limitations & Recommended Future Work

1. **Permanent Inaccessibility to Standard Bots:** Because Cloudflare Managed Challenges and WAF rules are controlled by the target domain administrators, automated crawlers operating under standard identifying headers cannot bypass them without authorization.
2. **Authorized Crawl Partnerships:** In future operational phases, prospects with bot protection can be invited to allowlist the ProspectOS crawler IP range or configure authorized site verification tokens.
3. **Headless Browser Rendering Consideration:** For authorized audit engagements (with explicit prospect consent), an enterprise headless rendering runner (e.g. Playwright with enterprise auth tokens) could be introduced in a future development phase.

---

## 8. Final Remediation Verdict

### **PASS WITH ISSUES**

- **Software Remediation:** **PASS** (Zero test regressions; 100/100 tests passing; accurate failure classification; full evidence fallback; calibrated scoring; zero on-page hallucinations).
- **Domain Accessibility:** **ISSUES (EXPECTED)** (The 3 target domains remain access-restricted by third-party Cloudflare WAF bot challenges. The platform now handles, records, and reports these restrictions transparently without compromising data integrity).

*The remediation is complete. No further phases, outreach, or deployments have been initiated.*
