import os
import sys

# CRITICAL ISOLATION: Verification scripts must write to 'prospectos_test', NEVER production 'prospectos'
current_db = os.getenv("DATABASE_URL", "")
if "@db:5432" in current_db:
    TEST_DB = "postgresql+asyncpg://user:password@db:5432/prospectos_test"
else:
    TEST_DB = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/prospectos_test")

os.environ["DATABASE_URL"] = TEST_DB

from app.core.config import settings
settings.DATABASE_URL = TEST_DB

import asyncio
import httpx
import uuid
import datetime
import jwt
from sqlalchemy import text
from app.core.security import hash_password, SECRET_KEY, ALGORITHM
from app.db.session import async_session_maker
from app.models import PortalUser, Company, ClientReport, PortalAuditLog

BASE_URL = "http://localhost:8000"

async def run_auth_verification():
    print("=" * 80)
    print("PROSPECTOS PHASE 2: AUTHENTICATION & AUTHORIZATION RIGOROUS AUDIT")
    print("=" * 80)

    # Enforce safe database isolation
    async with async_session_maker() as verify_session:
        db_name = (await verify_session.execute(text("SELECT current_database();"))).scalar()
        if db_name == "prospectos":
            raise RuntimeError("SAFETY ABORT: Verification script refused to run against production database 'prospectos'!")
        print(f"Safety Check Passed: Connected to isolated testing database '{db_name}'.")

    results = {}

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Unauthenticated Requests to Admin Endpoints
        print("\n[1. Testing Unauthenticated Access to Admin Endpoints]")
        for endpoint in ["/admin/overview", "/admin/users", "/admin/roles", "/admin/settings", "/admin/scraper-infra/status"]:
            res = await client.get(endpoint)
            print(f"  • GET {endpoint} -> HTTP {res.status_code} ({res.json().get('detail')})")
            assert res.status_code == 401, f"Expected 401 for unauthenticated {endpoint}, got {res.status_code}"
        results["unauthenticated_rejection"] = "PASS (All return HTTP 401)"

        # 2. Invalid Token
        print("\n[2. Testing Invalid JWT Token]")
        res_invalid = await client.get("/admin/users", headers={"Authorization": "Bearer gibberish_token_12345"})
        print(f"  • GET /admin/users with invalid token -> HTTP {res_invalid.status_code} ({res_invalid.json().get('detail')})")
        assert res_invalid.status_code == 401, f"Expected 401 for invalid token, got {res_invalid.status_code}"
        results["invalid_token_rejection"] = "PASS (HTTP 401)"

        # 3. Expired Token
        print("\n[3. Testing Expired JWT Token]")
        expired_payload = {
            "sub": str(uuid.uuid4()),
            "email": "expired@prospectos.com",
            "role": "SUPER_ADMIN",
            "exp": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)
        }
        expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)
        res_expired = await client.get("/admin/users", headers={"Authorization": f"Bearer {expired_token}"})
        print(f"  • GET /admin/users with expired token -> HTTP {res_expired.status_code} ({res_expired.json().get('detail')})")
        assert res_expired.status_code == 401, f"Expected 401 for expired token, got {res_expired.status_code}"
        results["expired_token_rejection"] = "PASS (HTTP 401)"

        # 4. Role Authorization: CLIENT_USER attempting Admin Access
        print("\n[4. Testing Organization User (CLIENT_USER) RBAC Block on Admin APIs]")
        # Log in as client user or create a temporary client user
        suffix = uuid.uuid4().hex[:6]
        async with async_session_maker() as session:
            test_client_user = PortalUser(
                email=f"client_{suffix}@orgtest.com",
                full_name="Test Client User",
                hashed_password=hash_password("Pass1234!"),
                role="CLIENT_USER",
                is_active=True
            )
            session.add(test_client_user)
            await session.commit()
            await session.refresh(test_client_user)
            client_user_id = str(test_client_user.id)

        login_client = await client.post("/portal/auth/login", json={
            "email": f"client_{suffix}@orgtest.com",
            "password": "Pass1234!"
        })
        assert login_client.status_code == 200, f"Failed to login client user: {login_client.text}"
        client_token = login_client.json()["access_token"]

        for endpoint in ["/admin/overview", "/admin/users", "/admin/settings"]:
            res_client_role = await client.get(endpoint, headers={"Authorization": f"Bearer {client_token}"})
            print(f"  • CLIENT_USER GET {endpoint} -> HTTP {res_client_role.status_code} ({res_client_role.json().get('detail')})")
            assert res_client_role.status_code == 403, f"Expected 403 for CLIENT_USER on {endpoint}, got {res_client_role.status_code}"
        results["client_role_forbidden"] = "PASS (All return HTTP 403)"

        # 5. Role Authorization: AGENCY ADMIN attempting Super Admin APIs
        print("\n[5. Testing Agency Admin (ADMIN) RBAC Block on Super Admin APIs]")
        async with async_session_maker() as session:
            test_admin_user = PortalUser(
                email=f"agency_{suffix}@agencytest.com",
                full_name="Test Agency Admin",
                hashed_password=hash_password("AdminPass1234!"),
                role="ADMIN",
                is_active=True
            )
            session.add(test_admin_user)
            await session.commit()
            await session.refresh(test_admin_user)

        login_admin = await client.post("/portal/auth/login", json={
            "email": f"agency_{suffix}@agencytest.com",
            "password": "AdminPass1234!"
        })
        assert login_admin.status_code == 200, f"Failed to login agency admin: {login_admin.text}"
        agency_admin_token = login_admin.json()["access_token"]

        res_agency = await client.get("/admin/users", headers={"Authorization": f"Bearer {agency_admin_token}"})
        print(f"  • ADMIN role GET /admin/users -> HTTP {res_agency.status_code} ({res_agency.json().get('detail')})")
        assert res_agency.status_code == 403, f"Expected 403 for ADMIN role on Super Admin APIs, got {res_agency.status_code}"
        results["admin_role_forbidden"] = "PASS (HTTP 403)"

        # 6. Valid Super Admin Access
        print("\n[6. Testing Valid Super Admin Access]")
        login_super = await client.post("/portal/auth/login", json={
            "email": "infosaqlainseo@gmail.com",
            "password": "ProspectOS@SuperAdmin2026!"
        })
        assert login_super.status_code == 200, f"Failed to login super admin: {login_super.text}"
        super_token = login_super.json()["access_token"]

        res_super_overview = await client.get("/admin/overview", headers={"Authorization": f"Bearer {super_token}"})
        print(f"  • SUPER_ADMIN GET /admin/overview -> HTTP {res_super_overview.status_code}")
        assert res_super_overview.status_code == 200, f"Expected 200 for SUPER_ADMIN, got {res_super_overview.status_code}"

        res_super_users = await client.get("/admin/users", headers={"Authorization": f"Bearer {super_token}"})
        print(f"  • SUPER_ADMIN GET /admin/users -> HTTP {res_super_users.status_code} ({len(res_super_users.json())} users returned)")
        assert res_super_users.status_code == 200, f"Expected 200 for SUPER_ADMIN, got {res_super_users.status_code}"
        results["super_admin_access"] = "PASS (HTTP 200 on all endpoints)"

        # 7. Session Logout & Revocation
        print("\n[7. Testing Session Logout & Immediate Token Revocation]")
        # Issue a dedicated token to revoke
        login_to_revoke = await client.post("/portal/auth/login", json={
            "email": "infosaqlainseo@gmail.com",
            "password": "ProspectOS@SuperAdmin2026!"
        })
        token_to_revoke = login_to_revoke.json()["access_token"]

        # Confirm token works before logout
        before_logout = await client.get("/admin/overview", headers={"Authorization": f"Bearer {token_to_revoke}"})
        assert before_logout.status_code == 200, "Token failed before logout!"

        # Call logout endpoint
        res_logout = await client.post("/portal/auth/logout", headers={"Authorization": f"Bearer {token_to_revoke}"})
        print(f"  • POST /portal/auth/logout -> HTTP {res_logout.status_code} ({res_logout.json()})")
        assert res_logout.status_code == 200, f"Logout failed: {res_logout.text}"

        # Attempt to use the same token after logout
        after_logout = await client.get("/admin/overview", headers={"Authorization": f"Bearer {token_to_revoke}"})
        print(f"  • GET /admin/overview with revoked token -> HTTP {after_logout.status_code} ({after_logout.json().get('detail')})")
        assert after_logout.status_code == 401, f"Expected 401 for revoked token, got {after_logout.status_code}"
        assert "revoked" in after_logout.json().get("detail", "").lower()
        results["token_revocation"] = "PASS (Immediate 401 revocation enforced)"

    print("\n" + "=" * 80)
    print("AUTHENTICATION & AUTHORIZATION AUDIT RESULTS:")
    for test, status in results.items():
        print(f"  • {test:<30}: {status}")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_auth_verification())

