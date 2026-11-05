import os
import hmac
import hashlib
import secrets
import uuid
import jwt
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Union, Any
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.redis import get_redis
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

async def is_token_revoked(token: str, redis_client: Optional[Any] = None) -> bool:
    """Checks whether the token has been added to the session revocation blocklist in Redis."""
    if not redis_client or not token:
        return False
    try:
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        val = await redis_client.get(f"revoked_token:{token_hash}")
        return bool(val)
    except Exception:
        return False


async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    db: AsyncSession = Depends(get_db),
    redis_client: Optional[Any] = Depends(get_redis)
) -> PortalUser:
    """
    Extracts, verifies, and returns the authenticated PortalUser.
    Raises 401 Unauthorized if the token is missing, expired, or revoked.
    """
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if await is_token_revoked(auth.credentials, redis_client):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked or logged out. Please log in again.",
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
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account not found.")
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended or deactivated. Access denied. Please contact your administrator."
        )

    return user


def require_roles(allowed_roles: List[str]):
    """
    Dependency factory that enforces user role authorization.
    Allowed roles: SUPER_ADMIN, ADMIN, AGENCY_STAFF, CLIENT_USER
    SUPER_ADMIN inherently satisfies any administrative/staff role requirement.
    """
    async def role_checker(current_user: PortalUser = Depends(get_current_user)) -> PortalUser:
        if current_user.role == "SUPER_ADMIN":
            return current_user
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

# =========================================================================
# 4. SSRF Protection & Scraper API Key Management
# =========================================================================

import ipaddress
import socket
from urllib.parse import urlparse
from typing import Tuple

BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),       # Link-local & Cloud Metadata (169.254.169.254)
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),          # Multicast
    ipaddress.ip_network("240.0.0.0/4"),          # Reserved
    ipaddress.ip_network("255.255.255.255/32"),
    # IPv6
    ipaddress.ip_network("::/128"),
    ipaddress.ip_network("::1/128"),              # Loopback
    ipaddress.ip_network("fc00::/7"),             # Unique local
    ipaddress.ip_network("fe80::/10"),            # Link-local
    ipaddress.ip_network("ff00::/8"),             # Multicast
]

BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "metadata.internal",
    "instance-data",
    "169.254.169.254",
    "cloud.internal",
}

def validate_target_url(url: str) -> Tuple[bool, str, Optional[str]]:
    """
    Validates a user-provided target URL against SSRF vulnerabilities:
    - Verifies protocol is http or https
    - Checks host against known metadata / internal hostnames
    - Resolves DNS and checks resolved IP against blocked private/loopback/cloud CIDR ranges.
    Returns: (is_safe: bool, validated_url_or_error: str, resolved_ip: Optional[str])
    """
    if not url:
        return False, "URL cannot be empty.", None
    
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"Invalid URL structure: {e}", None

    if parsed.scheme not in ("http", "https"):
        return False, f"Unsupported scheme '{parsed.scheme}'. Only http and https are allowed.", None

    hostname = (parsed.hostname or "").lower().strip()
    if not hostname:
        return False, "URL must include a valid hostname.", None

    if hostname in BLOCKED_HOSTNAMES or hostname.endswith(".internal") or hostname.endswith(".local"):
        return False, f"Access to internal or cloud metadata hostname '{hostname}' is strictly forbidden.", None

    # Resolve hostname to IP addresses
    try:
        addr_info = socket.getaddrinfo(hostname, None)
        resolved_ips = list({item[4][0] for item in addr_info})
    except socket.gaierror:
        return False, f"Hostname '{hostname}' could not be resolved via DNS.", None
    except Exception as e:
        return False, f"DNS resolution failed: {e}", None

    if not resolved_ips:
        return False, f"No IP address found for host '{hostname}'.", None

    primary_ip = resolved_ips[0]
    for ip_str in resolved_ips:
        try:
            ip_obj = ipaddress.ip_address(ip_str)
            for network in BLOCKED_NETWORKS:
                if ip_obj in network:
                    return False, f"Access to private/internal IP address '{ip_str}' is forbidden for security (SSRF prevention).", ip_str
        except ValueError:
            return False, f"Invalid IP address format: {ip_str}", None

    return True, url, primary_ip


def generate_api_key(name: str) -> Tuple[str, str, str]:
    """Generates a secure API key with prefix, raw key, and hash."""
    random_part = secrets.token_urlsafe(32)
    raw_key = f"pos_live_{random_part}"
    prefix = raw_key[:14] + "..."
    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    return raw_key, prefix, key_hash

def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.strip().encode("utf-8")).hexdigest()

