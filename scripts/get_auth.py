#!/usr/bin/env python3
"""
ProspectOS - Get Authentication Credentials & JWT Bearer Token
Usage:
    python scripts/get_auth.py
"""
import sys
import asyncio
from pathlib import Path

# Setup paths
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.db.session import async_session_maker
from app.models import PortalUser
from app.services.reporting.report_service import hash_password, create_access_token, get_utc_now
from sqlalchemy import select

DEFAULT_EMAIL = "admin@grokxseo.com"
DEFAULT_PASSWORD = "AdminPassword123!"

async def get_or_create_admin():
    async with async_session_maker() as session:
        stmt = select(PortalUser).where(PortalUser.email == DEFAULT_EMAIL)
        admin = (await session.execute(stmt)).scalar_one_or_none()
        
        if not admin:
            admin = PortalUser(
                email=DEFAULT_EMAIL,
                hashed_password=hash_password(DEFAULT_PASSWORD),
                full_name="GrokxSEO Super Admin",
                role="ADMIN",
                is_active=True,
                created_at=get_utc_now(),
                updated_at=get_utc_now(),
            )
            session.add(admin)
            await session.commit()
            await session.refresh(admin)
            status_str = "Created New Admin User"
        else:
            admin.hashed_password = hash_password(DEFAULT_PASSWORD)
            admin.is_active = True
            await session.commit()
            status_str = "Existing Master Admin User"

        token = create_access_token(
            data={
                "sub": str(admin.id),
                "email": admin.email,
                "role": admin.role
            }
        )

        print("\n" + "="*60)
        print(" PROSPECTOS - AUTHENTICATION & ACCESS CREDENTIALS")
        print("="*60)
        print(f"Status:        {status_str}")
        print(f"User ID:       {admin.id}")
        print(f"Email:         {admin.email}")
        print(f"Password:      {DEFAULT_PASSWORD}")
        print(f"Role:          {admin.role}")
        print("-"*60)
        print("JWT ACCESS TOKEN (Bearer):")
        print(token)
        print("-"*60)
        print("API Header usage:")
        print(f"Authorization: Bearer {token}")
        print("\nExample curl test:")
        print(f"curl -H 'Authorization: Bearer {token}' http://localhost:8000/portal/auth/me")
        print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(get_or_create_admin())
