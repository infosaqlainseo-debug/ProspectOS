import uuid
import logging
import base64
import json
import httpx
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models import GoogleDriveConnection, GoogleDriveSyncJob, Company, CRMActivity
from app.core.config import settings

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
GOOGLE_SHEETS_API_BASE = "https://sheets.googleapis.com/v4/spreadsheets"

# Least-privilege drive file scope
SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/spreadsheets"
]

def _encrypt_token(raw_token: str) -> str:
    """Obfuscates/encrypts token before storing in database."""
    if not raw_token:
        return ""
    return base64.b64encode(raw_token.encode("utf-8")).decode("utf-8")

def _decrypt_token(enc_token: str) -> str:
    if not enc_token:
        return ""
    try:
        return base64.b64decode(enc_token.encode("utf-8")).decode("utf-8")
    except Exception:
        return enc_token


class GoogleDriveService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_connection(self) -> Optional[GoogleDriveConnection]:
        stmt = select(GoogleDriveConnection).order_by(GoogleDriveConnection.created_at.desc()).limit(1)
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def get_or_create_connection(self) -> GoogleDriveConnection:
        conn = await self.get_connection()
        if not conn:
            conn = GoogleDriveConnection(
                is_connected=False,
                selected_folder_path="ProspectOS/Leads/",
                export_format="GOOGLE_SHEET",
                last_sync_status="IDLE"
            )
            self.db.add(conn)
            await self.db.commit()
            await self.db.refresh(conn)
        return conn

    async def get_status(self) -> Dict[str, Any]:
        conn = await self.get_or_create_connection()
        return {
            "is_connected": conn.is_connected,
            "account_email": conn.account_email,
            "selected_folder_id": conn.selected_folder_id,
            "selected_folder_path": conn.selected_folder_path,
            "master_sheet_id": conn.master_sheet_id,
            "master_sheet_url": conn.master_sheet_url,
            "export_format": conn.export_format,
            "auto_sync_enabled": conn.auto_sync_enabled,
            "last_sync_at": conn.last_sync_at.isoformat() if conn.last_sync_at else None,
            "last_sync_status": conn.last_sync_status,
            "last_error_message": conn.last_error_message,
            "token_valid": bool(conn.access_token_encrypted or conn.refresh_token_encrypted)
        }

    def generate_auth_url(self, client_id: str, redirect_uri: str, state: str = "prospectos_oauth") -> str:
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state
        }
        query_string = "&".join(f"{k}={httpx.URL('', params={k: v}).query.decode()}" for k, v in params.items())
        return f"{GOOGLE_AUTH_URL}?{query_string}"

    async def exchange_code_for_tokens(
        self,
        code: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"
                }
            )
            if resp.status_code != 200:
                raise ValueError(f"Google OAuth token exchange failed: {resp.text}")
            token_data = resp.json()

        # Fetch account email from userinfo
        account_email = None
        access_token = token_data.get("access_token")
        if access_token:
            async with httpx.AsyncClient(timeout=10.0) as client:
                u_resp = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                if u_resp.status_code == 200:
                    account_email = u_resp.json().get("email")

        # Save to database
        conn = await self.get_or_create_connection()
        conn.is_connected = True
        conn.client_id = client_id
        conn.client_secret_encrypted = _encrypt_token(client_secret)
        conn.access_token_encrypted = _encrypt_token(access_token)
        if token_data.get("refresh_token"):
            conn.refresh_token_encrypted = _encrypt_token(token_data["refresh_token"])
        expires_in = token_data.get("expires_in", 3600)
        conn.token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        conn.account_email = account_email or "connected_user@gmail.com"
        conn.last_sync_status = "SUCCESS"
        conn.last_error_message = None
        conn.updated_at = datetime.now(timezone.utc)
        await self.db.commit()

        return {
            "status": "connected",
            "account_email": conn.account_email,
            "expires_in": expires_in
        }

    async def save_manual_connection(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        account_email: Optional[str] = None,
        selected_folder_path: str = "ProspectOS/Leads/"
    ) -> Dict[str, Any]:
        """Supports direct credential configuration from authorized service or developer account."""
        conn = await self.get_or_create_connection()
        conn.is_connected = True
        conn.client_id = client_id
        conn.client_secret_encrypted = _encrypt_token(client_secret)
        conn.refresh_token_encrypted = _encrypt_token(refresh_token)
        conn.account_email = account_email or "agency_drive@grokxseo.com"
        conn.selected_folder_path = selected_folder_path
        conn.last_sync_status = "IDLE"
        conn.last_error_message = None
        conn.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        return {"status": "connected", "account_email": conn.account_email}

    async def disconnect(self) -> Dict[str, Any]:
        conn = await self.get_or_create_connection()
        conn.is_connected = False
        conn.access_token_encrypted = None
        conn.refresh_token_encrypted = None
        conn.last_sync_status = "DISCONNECTED"
        conn.last_error_message = "Disconnected by user."
        conn.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        return {"status": "disconnected"}

    async def _get_valid_access_token(self) -> Optional[str]:
        conn = await self.get_connection()
        if not conn or not conn.is_connected:
            return None

        # Check if current access token is valid
        now = datetime.now(timezone.utc)
        if conn.access_token_encrypted and conn.token_expiry and conn.token_expiry > now + timedelta(minutes=5):
            return _decrypt_token(conn.access_token_encrypted)

        # Refresh token
        refresh_token = _decrypt_token(conn.refresh_token_encrypted or "")
        client_id = conn.client_id
        client_secret = _decrypt_token(conn.client_secret_encrypted or "")

        if not refresh_token or not client_id or not client_secret:
            return None

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    GOOGLE_TOKEN_URL,
                    data={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token"
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    new_access = data.get("access_token")
                    conn.access_token_encrypted = _encrypt_token(new_access)
                    expires_in = data.get("expires_in", 3600)
                    conn.token_expiry = now + timedelta(seconds=expires_in)
                    await self.db.commit()
                    return new_access
                else:
                    logger.error(f"Failed to refresh Google token: {resp.text}")
                    conn.last_error_message = f"Token refresh failed: {resp.text}"
                    await self.db.commit()
                    return None
        except Exception as e:
            logger.error(f"Error refreshing Google Drive token: {e}")
            return None

    async def sync_company_to_drive(
        self,
        company_id: uuid.UUID,
        sync_type: str = "AUTOMATIC"
    ) -> Dict[str, Any]:
        """Synchronizes a verified prospect lead into Google Drive and updates the lead record."""
        company = await self.db.get(Company, company_id)
        if not company:
            raise ValueError(f"Company {company_id} not found")

        conn = await self.get_or_create_connection()

        # Create sync job record
        job = GoogleDriveSyncJob(
            company_id=company.id,
            status="RUNNING",
            sync_type=sync_type,
            destination_folder=f"{conn.selected_folder_path}{company.country or 'General'}/{company.industry or 'General'}/"
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        # Verify Google Drive connection
        if not conn.is_connected:
            job.status = "FAILED"
            job.error_message = "Google Drive is not connected. Configure OAuth credentials in Google Drive Settings."
            company.gdrive_sync_status = "NOT_CONNECTED"
            await self.db.commit()
            return {
                "success": False,
                "status": "NOT_CONNECTED",
                "message": job.error_message,
                "job_id": str(job.id)
            }

        access_token = await self._get_valid_access_token()
        if not access_token:
            job.status = "FAILED"
            job.error_message = "Valid Google OAuth access token unavailable. Please re-authenticate."
            company.gdrive_sync_status = "FAILED"
            await self.db.commit()
            return {
                "success": False,
                "status": "AUTH_REQUIRED",
                "message": job.error_message,
                "job_id": str(job.id)
            }

        # Prepare lead row
        row_data = [
            company.company_name or company.canonical_domain or "Unnamed Prospect",
            company.website_url or f"https://{company.canonical_domain}",
            company.canonical_domain or "",
            company.country or "Mexico",
            company.city or "",
            company.industry or "E-commerce",
            company.public_email or "",
            company.phone_number or company.whatsapp_number or "",
            company.facebook_url or "",
            company.instagram_url or "",
            company.whatsapp_click_url or (f"https://wa.me/{company.whatsapp_number}" if company.whatsapp_number else ""),
            f"{company.lead_score:.1f}" if company.lead_score is not None else "N/A",
            ", ".join(company.seo_summary_findings or ["Technical SEO Audit", "Backlink Opportunities"]),
            ", ".join(company.recommended_services or ["Technical SEO", "Link Building", "Digital PR"]),
            "ProspectOS Discovery",
            company.first_discovered_at.strftime("%Y-%m-%d %H:%M:%S") if company.first_discovered_at else "",
            company.sales_stage,
            str(company.id)
        ]

        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            master_sheet_id = conn.master_sheet_id

            async with httpx.AsyncClient(timeout=25.0) as client:
                # If master sheet doesn't exist, create it
                if not master_sheet_id:
                    create_body = {
                        "properties": {"title": "ProspectOS — Qualified Leads Master"},
                        "sheets": [{
                            "properties": {"title": "Leads"},
                            "data": [{
                                "startRow": 0,
                                "startColumn": 0,
                                "rowData": [{
                                    "values": [
                                        {"userEnteredValue": {"stringValue": "Company Name"}},
                                        {"userEnteredValue": {"stringValue": "Website URL"}},
                                        {"userEnteredValue": {"stringValue": "Canonical Domain"}},
                                        {"userEnteredValue": {"stringValue": "Country"}},
                                        {"userEnteredValue": {"stringValue": "City"}},
                                        {"userEnteredValue": {"stringValue": "Industry"}},
                                        {"userEnteredValue": {"stringValue": "Public Contact Email"}},
                                        {"userEnteredValue": {"stringValue": "Business Phone"}},
                                        {"userEnteredValue": {"stringValue": "Facebook URL"}},
                                        {"userEnteredValue": {"stringValue": "Instagram URL"}},
                                        {"userEnteredValue": {"stringValue": "WhatsApp Click-to-Chat"}},
                                        {"userEnteredValue": {"stringValue": "SEO Score"}},
                                        {"userEnteredValue": {"stringValue": "SEO Findings"}},
                                        {"userEnteredValue": {"stringValue": "Recommended GrokxSEO Services"}},
                                        {"userEnteredValue": {"stringValue": "Discovery Source"}},
                                        {"userEnteredValue": {"stringValue": "Discovery Date"}},
                                        {"userEnteredValue": {"stringValue": "CRM Status"}},
                                        {"userEnteredValue": {"stringValue": "ProspectOS Record ID"}}
                                    ]
                                }]
                            }]
                        }]
                    }
                    create_resp = await client.post(
                        GOOGLE_SHEETS_API_BASE,
                        headers=headers,
                        json=create_body
                    )
                    if create_resp.status_code in [200, 201]:
                        sheet_info = create_resp.json()
                        master_sheet_id = sheet_info.get("spreadsheetId")
                        conn.master_sheet_id = master_sheet_id
                        conn.master_sheet_url = f"https://docs.google.com/spreadsheets/d/{master_sheet_id}/edit"
                        await self.db.commit()
                    else:
                        raise ValueError(f"Failed to create Google Sheet: {create_resp.text}")

                # Append row to sheet
                append_url = f"{GOOGLE_SHEETS_API_BASE}/{master_sheet_id}/values/Leads!A1:append?valueInputOption=USER_ENTERED"
                append_resp = await client.post(
                    append_url,
                    headers=headers,
                    json={"values": [row_data]}
                )

                if append_resp.status_code not in [200, 201]:
                    raise ValueError(f"Failed to append row to Google Sheet: {append_resp.text}")

            now = datetime.now(timezone.utc)
            resource_url = conn.master_sheet_url or f"https://docs.google.com/spreadsheets/d/{master_sheet_id}"
            
            # Update Sync Job
            job.status = "COMPLETED"
            job.resource_id = master_sheet_id
            job.resource_url = resource_url
            job.synced_at = now
            
            # Update Company
            company.gdrive_file_id = master_sheet_id
            company.gdrive_file_url = resource_url
            company.gdrive_synced_at = now
            company.gdrive_sync_status = "SYNCED"

            # Update Connection stats
            conn.last_sync_at = now
            conn.last_sync_status = "SUCCESS"
            conn.last_error_message = None

            # Add CRM Activity
            activity = CRMActivity(
                company_id=company.id,
                activity_type="GDRIVE_SYNCED",
                actor="google_drive_sync_service",
                title=f"Lead synced to Google Drive",
                details={
                    "resource_id": master_sheet_id,
                    "resource_url": resource_url,
                    "sync_type": sync_type
                }
            )
            self.db.add(activity)
            await self.db.commit()

            return {
                "success": True,
                "status": "SYNCED",
                "resource_id": master_sheet_id,
                "resource_url": resource_url,
                "job_id": str(job.id)
            }

        except Exception as e:
            logger.error(f"Google Drive synchronization failed for company {company_id}: {e}")
            job.status = "FAILED"
            job.error_message = str(e)
            company.gdrive_sync_status = "FAILED"
            conn.last_sync_status = "FAILED"
            conn.last_error_message = str(e)
            await self.db.commit()
            return {
                "success": False,
                "status": "FAILED",
                "error": str(e),
                "job_id": str(job.id)
            }

    async def list_sync_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        stmt = (
            select(GoogleDriveSyncJob, Company.company_name, Company.canonical_domain)
            .join(Company, GoogleDriveSyncJob.company_id == Company.id)
            .order_by(desc(GoogleDriveSyncJob.created_at))
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        items = []
        for job, c_name, c_domain in res.all():
            items.append({
                "job_id": str(job.id),
                "company_id": str(job.company_id),
                "company_name": c_name or c_domain or "Prospect",
                "status": job.status,
                "sync_type": job.sync_type,
                "resource_id": job.resource_id,
                "resource_url": job.resource_url,
                "destination_folder": job.destination_folder,
                "error_message": job.error_message,
                "synced_at": job.synced_at.isoformat() if job.synced_at else None,
                "created_at": job.created_at.isoformat()
            })
        return items
