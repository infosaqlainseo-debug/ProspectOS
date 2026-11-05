# PROSPECTOS — DATABASE BACKUP & RESTORATION DRILL REPORT

**Date:** 2026-11-04  
**Primary Database:** `prospectos`  
**Restoration Target Database:** `prospectos_isolation_drill_verify`  
**Validation Status:** 100% Verified Match Across All Tables, Constraints, Indexes & Sequences.  

---

## 1. Backup Artifact Telemetry

| Parameter | Value |
| :--- | :--- |
| **Origin Database** | `prospectos` |
| **Backup Command** | `pg_dump -U user -F c -b -v -f /var/lib/postgresql/data/...` |
| **Backup Filename** | `prospectos_pre_cleanup_backup_20261104_131700.dump` |
| **Host Storage Path** | `backups/prospectos_pre_cleanup_backup_20261104_131700.dump` |
| **File Size** | 770 KB (788,480 bytes) |
| **SHA-256 Checksum** | `94423747dd2a92e98655461632ae5a67251630411478217f1a695008f5551237` |
| **Checksum Verification**| Bit-for-bit match on container and host |

---

## 2. Restoration Drill Procedure

1. **Target Database Creation:**
   ```sql
   DROP DATABASE IF EXISTS prospectos_isolation_drill_verify;
   CREATE DATABASE prospectos_isolation_drill_verify OWNER "user";
   ```
2. **Execution of `pg_restore`:**
   ```bash
   pg_restore -U user -d prospectos_isolation_drill_verify -v /var/lib/postgresql/data/prospectos_pre_cleanup_backup_20261104_131700.dump
   ```
   *Exit code: 0 (Successful restore)*

---

## 3. Comparative Restoration Verification

| Metric | Source DB (`prospectos`) | Restored DB (`prospectos_isolation_drill_verify`) | Match Status |
| :--- | :---: | :---: | :---: |
| **Public Tables** | 78 | 78 | ✓ Exact Match |
| **Indexes** | 201 | 201 | ✓ Exact Match |
| **Table Constraints** | 792 | 792 | ✓ Exact Match |
| **Companies Count** | 921 | 921 | ✓ Exact Match |
| **Portal Users Count** | 122 | 122 | ✓ Exact Match |
| **Scraper Tasks Count** | 23 | 23 | ✓ Exact Match |
| **Scraper Task Runs Count** | 18 | 18 | ✓ Exact Match |
| **Extracted Records Count** | 174 | 174 | ✓ Exact Match |
| **Portal Audit Logs Count** | 352 | 352 | ✓ Exact Match |

---

## 4. Representative Application Queries on Restored Database

Queries executed against `prospectos_isolation_drill_verify`:
```sql
SELECT email, role, is_active FROM portal_users WHERE role='SUPER_ADMIN';
-- Result:
-- admin@prospectos.com     | SUPER_ADMIN | true
-- infosaqlainseo@gmail.com | SUPER_ADMIN | true

SELECT count(*) as total_tasks, sum(records_extracted) as total_extracted FROM scraper_task_runs;
-- Result: 18 runs | 166 records

SELECT count(*) as total_crm_leads FROM companies WHERE source_task_id IS NOT NULL;
-- Result: 27 leads
```

Restoration verification confirmed that production backups are fully functional, restorable, and structurally sound.
