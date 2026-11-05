import os
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import PortalUser, PortalAuditLog

logger = logging.getLogger(__name__)

async def bootstrap_super_admin(session: AsyncSession) -> dict:
    """
    Secure bootstrap mechanism for the initial Super Admin account.
    - Reads email and initial password from secure environment variables.
    - Does NOT hardcode credentials into version control or client bundles.
    - Idempotent: checks for existence before creation to prevent duplicate accounts.
    - Hashes password using PBKDF2-HMAC-SHA256 with cryptographic salt.
    - Creates an immutable security audit trail.
    """
    admin_email = os.getenv("SUPER_ADMIN_EMAIL", "infosaqlainseo@gmail.com").strip().lower()
    admin_password = os.getenv("SUPER_ADMIN_PASSWORD")

    stmt = select(PortalUser).where(PortalUser.email == admin_email)
    res = await session.execute(stmt)
    existing_user = res.scalar_one_or_none()

    if existing_user:
        # User already exists; ensure elevated SUPER_ADMIN status
        needs_commit = False
        if existing_user.role != "SUPER_ADMIN" or not existing_user.is_active:
            existing_user.role = "SUPER_ADMIN"
            existing_user.is_active = True
            needs_commit = True

        from app.core.security import verify_password
        if admin_password and not verify_password(admin_password, existing_user.hashed_password):
            existing_user.hashed_password = hash_password(admin_password)
            needs_commit = True
            logger.info(f"[BOOTSTRAP] Super Admin password updated from environment variable.")

        if needs_commit:
            await session.commit()
            logger.info(f"[BOOTSTRAP] Super Admin account '{admin_email}' reaffirmed as active SUPER_ADMIN.")
        return {
            "status": "EXISTS",
            "email": admin_email,
            "role": "SUPER_ADMIN",
            "user_id": str(existing_user.id)
        }

    # If no existing user and no password specified, generate secure random secret
    if not admin_password:
        import secrets
        admin_password = secrets.token_urlsafe(24)
        logger.warning(f"[BOOTSTRAP] No SUPER_ADMIN_PASSWORD provided. Generated random one-time password.")

    # Create initial Super Admin account
    hashed = hash_password(admin_password)
    new_admin = PortalUser(
        email=admin_email,
        full_name="Super Admin (Saqlain)",
        hashed_password=hashed,
        role="SUPER_ADMIN",
        is_active=True
    )
    session.add(new_admin)
    await session.flush()

    # Immutable security audit entry
    audit = PortalAuditLog(
        user_id=new_admin.id,
        action="BOOTSTRAP_INITIAL_SUPER_ADMIN",
        resource_type="USER",
        resource_id=str(new_admin.id),
        details={
            "email": admin_email,
            "role": "SUPER_ADMIN",
            "auth_method": "PBKDF2_HMAC_SHA256",
            "source": "ENVIRONMENT_BOOTSTRAP"
        }
    )
    session.add(audit)
    await session.commit()

    logger.info(f"[BOOTSTRAP] Initial Super Admin '{admin_email}' successfully registered and provisioned.")
    return {
        "status": "CREATED",
        "email": admin_email,
        "role": "SUPER_ADMIN",
        "user_id": str(new_admin.id)
    }

