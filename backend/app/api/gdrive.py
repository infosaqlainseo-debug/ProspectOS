import uuid
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models import Company
from app.services.gdrive.service import GoogleDriveService

router = APIRouter(prefix="/google-drive", tags=["google-drive"])


class ConnectOAuthRequest(BaseModel):
    code: str
    client_id: str
    client_secret: str
    redirect_uri: str


class ConnectManualRequest(BaseModel):
    client_id: str
    client_secret: str
    refresh_token: str
    account_email: Optional[str] = None
    selected_folder_path: str = "ProspectOS/Leads/"


class UpdateSettingsRequest(BaseModel):
    selected_folder_path: Optional[str] = None
    export_format: Optional[str] = None
    auto_sync_enabled: Optional[bool] = None


@router.get("/status")
async def get_gdrive_status(db: AsyncSession = Depends(get_db)):
    """Returns Google Drive connection status, destination folder, and sync health."""
    service = GoogleDriveService(db)
    return await service.get_status()


@router.get("/auth-url")
async def get_oauth_url(
    client_id: str,
    redirect_uri: str,
    state: str = "prospectos_oauth",
    db: AsyncSession = Depends(get_db)
):
    """Generates the official Google OAuth 2.0 authorization URL."""
    service = GoogleDriveService(db)
    url = service.generate_auth_url(client_id, redirect_uri, state)
    return {"auth_url": url}


@router.post("/connect/oauth")
async def connect_oauth(payload: ConnectOAuthRequest, db: AsyncSession = Depends(get_db)):
    """Exchanges an authorization code for Google Drive tokens."""
    service = GoogleDriveService(db)
    try:
        return await service.exchange_code_for_tokens(
            code=payload.code,
            client_id=payload.client_id,
            client_secret=payload.client_secret,
            redirect_uri=payload.redirect_uri
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/connect/manual")
async def connect_manual(payload: ConnectManualRequest, db: AsyncSession = Depends(get_db)):
    """Configures Google Drive with pre-authorized client credentials."""
    service = GoogleDriveService(db)
    return await service.save_manual_connection(
        client_id=payload.client_id,
        client_secret=payload.client_secret,
        refresh_token=payload.refresh_token,
        account_email=payload.account_email,
        selected_folder_path=payload.selected_folder_path
    )


@router.post("/disconnect")
async def disconnect_drive(db: AsyncSession = Depends(get_db)):
    """Disconnects Google Drive integration and clears stored tokens."""
    service = GoogleDriveService(db)
    return await service.disconnect()


@router.post("/settings")
async def update_settings(payload: UpdateSettingsRequest, db: AsyncSession = Depends(get_db)):
    """Updates Google Drive export configuration."""
    service = GoogleDriveService(db)
    conn = await service.get_or_create_connection()
    if payload.selected_folder_path is not None:
        conn.selected_folder_path = payload.selected_folder_path
    if payload.export_format is not None:
        conn.export_format = payload.export_format
    if payload.auto_sync_enabled is not None:
        conn.auto_sync_enabled = payload.auto_sync_enabled
    await db.commit()
    return await service.get_status()


@router.post("/sync/{company_id}")
async def sync_company(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Manually triggers synchronization of a specific company to Google Drive."""
    service = GoogleDriveService(db)
    try:
        result = await service.sync_company_to_drive(company_id, sync_type="MANUAL")
        return result
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-all")
async def sync_all_eligible_leads(
    limit: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Batch synchronizes eligible qualified leads into Google Drive."""
    service = GoogleDriveService(db)
    status = await service.get_status()
    if not status["is_connected"]:
        raise HTTPException(status_code=400, detail="Google Drive is not connected. Configure credentials in settings.")

    # Find leads with gdrive_sync_status != 'SYNCED'
    stmt = (
        select(Company.id)
        .where(Company.gdrive_sync_status != "SYNCED")
        .limit(limit)
    )
    ids = (await db.execute(stmt)).scalars().all()

    synced = []
    failed = []
    for cid in ids:
        res = await service.sync_company_to_drive(cid, sync_type="MANUAL_BATCH")
        if res.get("success"):
            synced.append(str(cid))
        else:
            failed.append({"id": str(cid), "error": res.get("error")})

    return {
        "total_queued": len(ids),
        "synced_count": len(synced),
        "failed_count": len(failed),
        "synced_ids": synced,
        "failed": failed
    }


@router.get("/jobs")
async def list_sync_jobs(limit: int = Query(50, ge=1, le=200), db: AsyncSession = Depends(get_db)):
    """Lists recent Google Drive synchronization jobs and export records."""
    service = GoogleDriveService(db)
    return await service.list_sync_jobs(limit)
