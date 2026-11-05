# PROSPECTOS — MULTI-TENANT RBAC & ACCESS CONTROL REPORT

**Date:** 2026-11-04  
**Scope:** Backend Role-Based Access Control, Tenant Isolation, and Session Middleware.  

---

## 1. Role Hierarchy & Access Matrix

ProspectOS enforces four fundamental user roles at the API layer:

| Role | Admin Control Center (`/admin/*`) | Client Portal (`/portal/*`) | Workspace Root (`/`) | Scraper Execution | Data Export |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `SUPER_ADMIN` | Full Access | Full Access | Full Access | Yes | Yes |
| `ORGANIZATION_ADMIN` / `ADMIN` | 403 Forbidden | Own Org Only | Own Org Only | Yes | Yes |
| `CLIENT_USER` / `STANDARD_USER` | 403 Forbidden | Read/Write Reports | Restricted Workspace | Scraper Read-Only | Restricted |
| `SUSPENDED_USER` (`is_active=False`) | 403 Forbidden | 403 Forbidden | 403 Forbidden | 403 Forbidden | 403 Forbidden |

---

## 2. Empirical RBAC Enforcement Proof

All authorization checks are enforced by backend middleware (`require_roles` and `get_current_user` in `backend/app/core/security.py`), not by frontend route hiding.

### Test Results Executed Against Live Backend:
1. **Unauthenticated Request:**
   - `GET /admin/overview` with no Authorization header -> **HTTP 401 Unauthorized**  
     `{"detail": "Authentication required. Please provide a valid Bearer token."}`
2. **Invalid Token Request:**
   - `GET /admin/users` with random token -> **HTTP 401 Unauthorized**  
     `{"detail": "Invalid or expired authentication token."}`
3. **Expired Token Request:**
   - `GET /admin/users` with expired JWT -> **HTTP 401 Unauthorized**  
     `{"detail": "Invalid or expired authentication token."}`
4. **Non-Admin User (Role: `MANAGER`):**
   - `GET /admin/overview` with Manager token -> **HTTP 403 Forbidden**  
     `{"detail": "Access denied. Required role in ['SUPER_ADMIN'], your role is 'MANAGER'."}`
5. **Super Admin User (Role: `SUPER_ADMIN`):**
   - `GET /admin/overview` with Super Admin token -> **HTTP 200 OK**  
     Returns full administrative dashboard payload.
6. **Suspended User (`is_active = False`):**
   - Request with suspended token -> **HTTP 403 Forbidden**  
     `{"detail": "Account is suspended or deactivated. Access denied. Please contact your administrator."}`

---

## 3. Login Redirection Behavior

Verified in `frontend/src/app/login/page.tsx`:
- `SUPER_ADMIN` -> Redirects automatically to `/admin`
- `ADMIN` / `ORGANIZATION_ADMIN` -> Redirects to `/portal`
- `CLIENT_USER` / `STANDARD_USER` -> Redirects to `/`

