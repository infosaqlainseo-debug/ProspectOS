# PROSPECTOS — TEST ENVIRONMENT & DATABASE ISOLATION REPORT

**Date:** 2026-11-04  
**Subject:** Architectural Database Separation, Connection Guarding, and Automated Prevention of Production Contamination.  

---

## 1. The Isolation Architecture

To ensure that automated tests, QA suites, and verification scripts can NEVER write into the production database `prospectos`, a multi-layer isolation system has been enacted:

```
[ Automated Tests (pytest) / Verification Scripts ]
                       │
                       ▼
        [ conftest.py / Script Guard ]
                       │
       Does target DB == "prospectos"?
              │                 │
             YES               NO
              │                 │
              ▼                 ▼
   [ FATAL RuntimeError ]   [ Target: prospectos_test ]
    (Immediate Abort)                   │
                                        ▼
                             [ PostgreSQL Catalog: ]
                              • prospectos_test (Isolated)
                              • prospectos (Untouched)
```

---

## 2. Implementation Details

### 2.1 `backend/tests/conftest.py`
1. Re-routes `os.environ["DATABASE_URL"]` and `settings.DATABASE_URL` to `prospectos_test` before any application modules are imported.
2. Monkey-patches `app.db.session.engine` and `async_session_maker` with `test_engine`.
3. Defines an `autouse=True` fixture `enforce_test_database_isolation`:
   ```python
   @pytest_asyncio.fixture(autouse=True)
   async def enforce_test_database_isolation():
       async with test_engine.connect() as conn:
           res = await conn.execute(text("SELECT current_database();"))
           active_db = res.scalar()
           if active_db != "prospectos_test":
               raise RuntimeError(
                   f"FATAL SAFETY VIOLATION: Test suite attempted to connect to database '{active_db}'. "
                   "Automated tests are strictly forbidden from connecting to 'prospectos'."
               )
   ```

### 2.2 Verification Scripts Guard
All verification scripts (`run_real_scraper_and_crm_verification.py`, `run_phase3_full_verification.py`, `verify_auth_and_rbac.py`) explicitly configure `settings.DATABASE_URL = .../prospectos_test` and assert that `SELECT current_database()` is NOT `prospectos`.

---

## 3. Empirical Proof of Isolation

1. **Test Execution:**
   - Ran 123 backend pytest tests (`pytest tests/`).
   - Ran live scraper verification (`run_real_scraper_and_crm_verification.py`).
2. **Post-Execution Database Inspection:**
   - Database `prospectos_test`: Received test tasks, test runs, and test companies.
   - Database `prospectos` (Production):
     - `companies`: **0**
     - `scraper_tasks`: **0**
     - `scraper_task_runs`: **0**
     - `extracted_records`: **0**
     - `portal_users`: **3** (Only genuine Super Admins and Staff)
3. **Conclusion:** Zero cross-contamination. Absolute environment isolation verified.
