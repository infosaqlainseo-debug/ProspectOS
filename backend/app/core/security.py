import os
import hmac
import hashlib
import secrets
import uuid
import jwt
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Union
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.db.session import get_db
from app.models import PortalUser, PortalAuditLog

# Secret key for JWT signing
SECRET_KEY = getattr(settings, "SECRET_KEY", "prospectos-phase3-4-secret-key-portal-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

security_bearer = HTTPBearer(auto_error=False)


# =========================================================================
# 1. Cryptographic Password Hashing & Verification
# =========================================================================

def hash_password(password: str) -> str:
    """Hashes a password using PBKDF2-HMAC-SHA256 with a unique cryptographic salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"{salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the salted PBKDF2 hash using constant-time comparison."""
    try:
        salt, key_hex = hashed_password.split("$", 1)
        check_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return hmac.compare_digest(check_key.hex(), key_hex)
    except Exception:
        return False


def generate_secure_token() -> str:
    """Generates an unguessable 32-byte hexadecimal invitation/session token."""
    return secrets.token_urlsafe(32)


# =========================================================================
# 2. JWT Generation & Decoding
# =========================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JSON Web Token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decodes and validates a JWT signature and expiration."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None


# =========================================================================
# 3. Authentication & Authorization FastAPI Dependencies
# =========================================================================

async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    db: AsyncSession = Depends(get_db)
) -> PortalUser:
    """
    Extracts, verifies, and returns the authenticated PortalUser.
    Raises 401 Unauthorized if the token is missing or invalid.
    """
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(auth.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed token payload.")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID in token.")

    user = await db.get(PortalUser, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account not found or deactivated.")

    return user


def require_roles(allowed_roles: List[str]):
    """
    Dependency factory that enforces user role authorization.
    Allowed roles: ADMIN, AGENCY_STAFF, CLIENT_USER
    """
    async def role_checker(current_user: PortalUser = Depends(get_current_user)) -> PortalUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role in {allowed_roles}, your role is '{current_user.role}'."
            )
        return current_user
    return role_checker


async def enforce_client_isolation(
    user: PortalUser,
    target_company_id: uuid.UUID,
    db: AsyncSession,
    action: str = "ACCESS_COMPANY_RESOURCE"
) -> bool:
    """
    CRITICAL SECURITY CHECK:
    Prevents cross-client data exposure.
    If the authenticated user is a CLIENT_USER, their company_id MUST match target_company_id.
    Logs unauthorized attempts directly to PortalAuditLog.
    """
    if user.role == "CLIENT_USER":
        if not user.company_id or user.company_id != target_company_id:
            # Audit unauthorized access attempt
            audit = PortalAuditLog(
                user_id=user.id,
                company_id=user.company_id,
                action="UNAUTHORIZED_ACCESS_ATTEMPT",
                resource_type="COMPANY",
                resource_id=str(target_company_id),
                details={
                    "attempted_target_company_id": str(target_company_id),
                    "user_assigned_company_id": str(user.company_id),
                    "action": action
                }
            )
            db.add(audit)
            await db.commit()

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cross-client access is strictly forbidden. You may only view data for your authorized company."
            )
    return True
