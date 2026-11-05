# PROSPECTOS — AUTHORIZED PRODUCTION DATA CLEANUP REPORT

**Date:** 2026-11-04  
**Database Executed Upon:** `prospectos` (Production PostgreSQL)  
**Execution Script:** `backend/scripts/execute_controlled_production_cleanup.py --execute-production`  
**Deletion Manifest:** `backend/exports/production_cleanup_manifest_20261104.json`  

---

## 1. Safety Pre-Conditions & Authorization

Prior to executing the cleanup:
1. Complete binary database snapshot was taken:
   - Filename: `prospectos_pre_cleanup_backup_20261104_131700.dump`
   - Size: 770 KB
   - SHA-256: `94423747dd2a92e98655461632ae5a67251630411478217f1a695008f5551237`
2. Restoration drill into isolated database `prospectos_isolation_drill_verify` verified 100% schema and table matching.
3. Test dry-run transaction executed with zero foreign key violations.

---

## 2. Pre-Cleanup vs Post-Cleanup Database Record Counts

| Database Table | Pre-Cleanup Count | Post-Cleanup Count | Records Removed | Records Preserved |
| :--- | :---: | :---: | :---: | :---: |
| `scraper_tasks` | 23 | 0 | 23 | 0 (New clean workspace) |
| `scraper_task_runs` | 18 | 0 | 18 | 0 |
| `extracted_records` | 174 | 0 | 174 | 0 |
| `companies` | 921 | 0 | 921 | 0 |
| `portal_users` | 122 | 3 | 119 | 3 (2 Super Admins + 1 Staff) |
| `portal_audit_logs` | 352 | 353 | 0 | 353 (352 historical + 1 cleanup audit) |
| `seo_global_configs` | 1 | 1 | 0 | 1 (Preserved) |
| `role_permissions` | 5 | 5 | 0 | 5 (Preserved) |
| `seo_public_pages` | 5 | 5 | 0 | 5 (Preserved) |
| `alembic_version` | 1 | 1 | 0 | 1 (`g1a2b3c4d5e6`) |

---

## 3. Preservation of Administrative Accounts & Audit Logs

### 3.1 Preserved Accounts
- `admin@prospectos.com` (UUID `7335313a-c6e5-499d-8fe4-3f200f3055ae`) — Role: `SUPER_ADMIN`
- `infosaqlainseo@gmail.com` (UUID `9a038bc5-ca67-4569-b087-8cb42dd98e42`) — Role: `SUPER_ADMIN`
- `lead.scout@prospectos.com` (UUID `cda0d139-52de-43c7-a3f7-57f58ba622d9`) — Role: `MANAGER`

### 3.2 Audit Log Integrity
No audit log rows were deleted. Foreign keys on `portal_audit_logs` pointing to deleted test users or companies were cleanly uncoupled (`SET NULL`), preserving the complete security audit history:
- Total audit logs retained: 353 entries.
- Added administrative audit entry: `AUTHORIZED_PRODUCTION_TEST_DATA_CLEANUP`.

---

## 4. Deletion Order & Foreign Key Compliance

The deletion executed within a single ACID transaction (`engine.begin()`) in the following strict dependency order:
1. `export_jobs` (1)
2. `extracted_records` (174)
3. `scraper_task_runs` (18)
4. `report_delivery_logs`, `client_reports` (72), `client_invitations` (10), `report_schedules` (11)
5. `google_drive_sync_jobs` (32), `social_message_logs` (10)
6. `crm_feedback_logs` (15), `crm_ai_research` (15), `crm_custom_fields`, `crm_segment_members`
7. `crm_notes` (10), `crm_tasks` (10), `crm_activities` (538), `crm_deals` (340)
8. `outreach_messages` (10), `outreach_drafts` (70), `outreach_suppressions` (10), `outreach_campaigns` (20)
9. `media_plan_items` (49), `media_plans` (49), `match_results` (40), `shortlist_items`, `shortlists`
10. `matching_runs` (40), `campaign_profiles` (30)
11. `publisher_quality_findings`, `publisher_quality_scores`, `publisher_observations`, `publisher_refresh_logs`, `publisher_records` (210), `import_audit_rows` (30), `import_batches` (10)
12. `sales_intelligence_scores` (70), `sales_opportunities` (220), `sales_briefs` (40), `opportunity_profiles` (50)
13. `competitive_analysis_runs` (30), `company_competitors` (50), `company_contacts` (30)
14. `discoveries` (22), `domains` (32), `evidence` (588), `health_assessments`, `historical_snapshots` (9), `seo_metrics` (79), `social_profiles`, `website_scans` (421), `risk_assessments`, `revenue_analytics_snapshots`
15. `agent_runs`, `job_results` (22), `errors`, `provider_usage` (36), `ai_contradictions`, `ai_observations` (20), `ai_extraction_runs` (20), `jobs` (156), `workflow_runs` (80), `workflows` (80)
16. `portal_audit_logs` FK uncoupling (`company_id = NULL`, test `user_id = NULL`)
17. `portal_users` (`company_id = NULL`, test users deleted)
18. `companies` (921 deleted)
19. `scraper_tasks` (23 deleted)
20. Administrative audit record inserted into `portal_audit_logs`.
21. Transaction committed.

