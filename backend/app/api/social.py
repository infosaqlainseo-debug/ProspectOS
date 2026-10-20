import uuid
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.outreach.social_service import SocialOutreachService

router = APIRouter(tags=["social-outreach"])


class SocialConnectionUpdateRequest(BaseModel):
    account_name: str
    account_id: Optional[str] = None
    phone_number: Optional[str] = None
    access_token: Optional[str] = None
    messaging_enabled: bool = False
    settings_data: Optional[Dict[str, Any]] = None


class SendSocialMessageRequest(BaseModel):
    company_id: uuid.UUID
    channel: str = Field(..., pattern="^(FACEBOOK|INSTAGRAM|WHATSAPP|facebook|instagram|whatsapp)$")
    message_text: str = Field(..., min_length=1)
    recipient_identifier: str = Field(..., min_length=1)
    explicit_user_confirmed: bool = False
    contact_id: Optional[uuid.UUID] = None


@router.get("/social-connections")
async def list_social_connections(db: AsyncSession = Depends(get_db)):
    """Returns connection status, permissions, and messaging capabilities for Facebook, Instagram, and WhatsApp."""
    service = SocialOutreachService(db)
    return await service.list_connections()


@router.post("/social-connections/{channel}/connect")
async def connect_social_channel(
    channel: str,
    payload: SocialConnectionUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Configures or updates a social account connection."""
    service = SocialOutreachService(db)
    try:
        return await service.update_connection(
            channel=channel,
            account_name=payload.account_name,
            account_id=payload.account_id,
            phone_number=payload.phone_number,
            access_token=payload.access_token,
            messaging_enabled=payload.messaging_enabled,
            settings_data=payload.settings_data
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.post("/social-connections/{channel}/disconnect")
async def disconnect_social_channel(channel: str, db: AsyncSession = Depends(get_db)):
    """Disconnects a social channel and safely clears credentials."""
    service = SocialOutreachService(db)
    return await service.disconnect_connection(channel)


@router.get("/outreach/multi-channel-drafts/{company_id}")
async def get_multi_channel_drafts(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Generates personalized, evidence-grounded drafts for Facebook, Instagram, WhatsApp, and Email."""
    service = SocialOutreachService(db)
    try:
        return await service.generate_multi_channel_drafts(company_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/outreach/social-message")
async def send_or_prepare_social_message(
    payload: SendSocialMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Unified outreach dispatcher.
    Requires explicit user confirmation to mark as sent, otherwise generates click-to-chat or prepared status.
    """
    service = SocialOutreachService(db)
    try:
        return await service.record_or_send_social_message(
            company_id=payload.company_id,
            channel=payload.channel,
            message_text=payload.message_text,
            recipient_identifier=payload.recipient_identifier,
            explicit_user_confirmed=payload.explicit_user_confirmed,
            contact_id=payload.contact_id
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/outreach/social-messages/{company_id}")
async def list_social_messages(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Lists history of social touches, WhatsApp click-to-chat actions, and messages for a company."""
    service = SocialOutreachService(db)
    return await service.list_company_messages(company_id)
