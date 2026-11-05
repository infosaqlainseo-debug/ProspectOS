# PROSPECTOS — APPLICATION SECURITY & CREDENTIAL AUDIT

**Date:** 2026-11-04  
**Scope:** Authentication, Credential Salting, Session Revocation, Account Lockout, Quick Fill Removal, and Secret Exposure Checks.  

---

## 1. Credential Security & Salting

### 1.1 Super Admin Credentials
- Passwords rotated with cryptographically unique salts.
- Evaluated with PBKDF2-HMAC-SHA256 (`backend/app/core/security.py`).
- Salt verification on live database `prospectos`:
  - `admin@prospectos.com`: salt prefix `1b15142d9b42d27`
  - `infosaqlainseo@gmail.com`: salt prefix `0e64157420be474`
- Zero shared default passwords. No password hashes returned in API responses.

### 1.2 Session Revocation & Redis Blacklisting
- Tested endpoint: `POST /portal/auth/logout`.
- Upon logout, access token is written to Redis key `revoked_token:<jti_or_token>` with remaining JWT TTL.
- Verified test:
  - Pre-logout: `GET /admin/overview` returned HTTP 200.
  - Post-logout: `GET /admin/overview` returned HTTP 401 (`"Session has been revoked or logged out. Please log in again."`).

---

## 2. Brute Force Protection & Account Lockout

- **Lockout Policy:** 5 consecutive failed login attempts locks account for 900 seconds (15 minutes).
- **Audit Preservation:** Failed login events are preserved as immutable audit records in `portal_audit_logs`.
- **Administrative Unlock:** Admin unlock action clears failed counter without deleting historical security logs, logging an explicit `ACCOUNT_UNLOCKED` audit event.

---

## 3. Production Quick Fill & Frontend Security

- **Quick Fill Removal:**
  - Audited `frontend/src/app/login/page.tsx`: 0 instances of demonstration Quick Fill or hardcoded credentials.
- **Compiled JavaScript Bundle Audit:**
  - Searched production `.next/` build artifacts for embedded passwords or tokens: 0 secrets found.
- **API Response Sanitization:**
  - Verified `AdminUserItem` schema: `hashed_password` is strictly omitted from Pydantic schemas.

---

## 4. SSRF & URL Validation Guard

- Scraper URL validator (`validate_target_url`):
  - Normalizes URLs using strict scheme parsing (`http`, `https`).
  - Resolves target hostnames against DNS and verifies that IP is NOT private, loopback (`127.0.0.1`), link-local (`169.254.169.254`), or multicast.
  - Test case: `https://quotes.toscrape.com` resolved to safe external IP `35.211.122.109`.

