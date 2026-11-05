# PROSPECTOS — CLOUDFLARE D1 DATABASE MIGRATION SPECIFICATION

**Target Engine**: Cloudflare D1 (SQLite 3 Edge Relational Database)  
**Database Name**: `prospectos-production-d1`  
**Database ID**: `62d68ef1-ed9d-47bf-b90a-8a26f2cfabe0`  
**Foreign Key Integrity**: `PRAGMA foreign_key_check: PASS (0 violations)`  

---

## 1. SCHEMA TRANSLATION RULES

| PostgreSQL Type | Cloudflare D1 (SQLite) Type | Handling Details |
| :--- | :--- | :--- |
| `UUID(as_uuid=True)` | `TEXT` | Stored as 36-char canonical hyphenated string |
| `JSONB` / `JSON` | `TEXT` | Stored as serialized JSON string; queried via `json_extract()` |
| `DateTime(timezone=True)` | `TEXT` | Stored as ISO-8601 UTC string (`YYYY-MM-DDTHH:MM:SS.sssZ`) |
| `Boolean` | `INTEGER` | Stored as `1` (true) or `0` (false) |
| `Float` / `Numeric` | `REAL` | IEEE 754 floating point |
| `Integer` / `BigInteger` | `INTEGER` | 64-bit signed integer |

---

## 2. RECONCILIATION AUDIT

| Table | PostgreSQL Rows | D1 Remote Rows | Integrity Status |
| :--- | :--- | :--- | :--- |
| `portal_users` | 3 | 3 | **MATCH (100%)** |
| `portal_audit_logs` | 355 | 355 | **MATCH (100%)** |
| `role_permissions` | 5 | 5 | **MATCH (100%)** |
| `ai_provider_settings` | 4 | 4 | **MATCH (100%)** |
| `seo_global_configs` | 1 | 1 | **MATCH (100%)** |
| `seo_public_pages` | 5 | 5 | **MATCH (100%)** |
| `scraper_api_keys` | 1 | 1 | **MATCH (100%)** |
| `sources` | 1 | 1 | **MATCH (100%)** |
| `google_drive_connections` | 1 | 1 | **MATCH (100%)** |
| `social_connections` | 1 | 1 | **MATCH (100%)** |

