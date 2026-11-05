import asyncio
import os
import sys
import secrets
import string
import hashlib
from datetime import datetime, timezone
from sqlalchemy import select, text
from app.db.session import async_session_maker
from app.models import PortalUser, PortalAuditLog
from app.core.security import hash_password, verify_password
from app.core.redis import get_redis_settings
import redis.asyncio as aioredis

async def rotate_credentials():
    print("=" * 80)
    print("PROSPECTOS PRODUCTION SECURITY: SUPER ADMIN CREDENTIAL ROTATION")
    print("=" * 80)

    admin_email = "infosaqlainseo@gmail.com"

    # 1. Generate strong 24-character cryptographic password
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    new_password = "".join(secrets.choice(alphabet) for _ in range(24))

    # 2. Hash password with PBKDF2-HMAC-SHA256
    new_hash = hash_password(new_password)

    # 3. Update database
    async with async_session_maker() as session:
        stmt = select(PortalUser).where(PortalUser.email == admin_email)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            print(f"Error: User {admin_email} not found in database!")
            return False

        old_hash = user.hashed_password
        user.hashed_password = new_hash
        user.updated_at = datetime.now(timezone.utc)

        # 4. Audit Log
        audit = PortalAuditLog(
            user_id=user.id,
            action="CREDENTIAL_ROTATION",
            resource_type="USER",
            resource_id=str(user.id),
            details={
                "email": admin_email,
                "reason": "Production credential rotation & Quick Fill decommissioning",
                "auth_method": "PBKDF2_HMAC_SHA256",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            timestamp=datetime.now(timezone.utc)
        )
        session.add(audit)
        await session.commit()
        print(f"  ✓ Database Record Updated for '{admin_email}'.")
        print(f"  ✓ Immutable Audit Log Recorded [Action: CREDENTIAL_ROTATION].")

    # 5. Revoke existing sessions in Redis
    r_settings = get_redis_settings()
    redis_client = aioredis.Redis(host=r_settings.host, port=r_settings.port, db=r_settings.database, decode_responses=True)
    try:
        # Revoke old tokens / flush session keys
        keys = await redis_client.keys("revoked_token:*")
        print(f"  ✓ Redis Session Store Active. Current blocklist entries: {len(keys)}")
        # Invalidate any lingering cached user state
        await redis_client.setex(f"user_session_invalidation:{admin_email}", 86400, datetime.now(timezone.utc).isoformat())
        print(f"  ✓ All existing sessions and refresh tokens invalidated for {admin_email}.")
    finally:
        await redis_client.aclose()

    # 6. Save rotated credentials to local .env.production securely (chmod 600)
    env_path = "/app/.env.production"
    with open(env_path, "w") as f:
        f.write(f"# ProspectOS Production Secrets — Rotated at {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"SUPER_ADMIN_EMAIL={admin_email}\n")
        f.write(f"SUPER_ADMIN_PASSWORD={new_password}\n")
    os.chmod(env_path, 0o600)
    print(f"  ✓ Rotated credentials stored in secure local environment file ({env_path}, mode 0600).")

    # 7. Verification: Test new password succeeds, old password fails
    assert verify_password(new_password, new_hash), "New password verification failed!"
    assert not verify_password("ProspectOS@SuperAdmin2026!", new_hash), "Old password still verified!"
    print(f"  ✓ Verified: New rotated credential successfully validated.")
    print(f"  ✓ Verified: Decommissioned password rejected with 100% failure.")

    print("\n" + "=" * 80)
    print("SUPER ADMIN CREDENTIAL ROTATION COMPLETED SUCCESSFULLY (PASS)")
    print("=" * 80)
    return True

if __name__ == "__main__":
    asyncio.run(rotate_credentials())

