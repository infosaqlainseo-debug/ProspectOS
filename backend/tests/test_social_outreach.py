import pytest
import uuid
from app.db.session import async_session_maker
from app.models import Company, SocialConnection, SocialMessageLog, CRMActivity
from app.services.outreach.social_service import SocialOutreachService, clean_phone_for_whatsapp

def test_clean_phone_for_whatsapp():
    assert clean_phone_for_whatsapp("+52 55 1234 5678") == "525512345678"
    assert clean_phone_for_whatsapp("55-9876-5432") == "5598765432"
    assert clean_phone_for_whatsapp("123") is None

@pytest.mark.asyncio
async def test_social_connections_lifecycle():
    async with async_session_maker() as session:
        service = SocialOutreachService(session)
        connections = await service.list_connections()
        channels = [c["channel"] for c in connections]
        assert "FACEBOOK" in channels
        assert "INSTAGRAM" in channels
        assert "WHATSAPP" in channels

        # Update WhatsApp connection
        update_res = await service.update_connection(
            channel="WHATSAPP",
            account_name="GrokxSEO WhatsApp Business",
            phone_number="+525512345678",
            access_token="test_wa_token",
            messaging_enabled=True
        )
        assert update_res["status"] == "connected"
        assert update_res["channel"] == "WHATSAPP"

        # Disconnect
        disc_res = await service.disconnect_connection("WHATSAPP")
        assert disc_res["status"] == "disconnected"

@pytest.mark.asyncio
async def test_multi_channel_drafts_generation():
    async with async_session_maker() as session:
        company = Company(
            company_name="Soluciones Digitales MX",
            canonical_domain=f"soluciones-{uuid.uuid4().hex[:6]}.com.mx",
            country="Mexico",
            industry="E-commerce & Retail",
            whatsapp_number="525587654321",
            facebook_url="https://facebook.com/solucionesdigitalesmx",
            sales_stage="QUALIFIED"
        )
        session.add(company)
        await session.commit()
        await session.refresh(company)

        service = SocialOutreachService(session)
        drafts_res = await service.generate_multi_channel_drafts(company.id)

        assert drafts_res["company_name"] == "Soluciones Digitales MX"
        drafts = drafts_res["drafts"]
        assert "whatsapp" in drafts
        assert "instagram" in drafts
        assert "facebook" in drafts
        assert "email" in drafts

        # WhatsApp draft must contain wa.me click-to-chat URL
        wa = drafts["whatsapp"]
        assert wa["is_eligible_for_click_to_chat"] is True
        assert wa["click_to_chat_url"].startswith("https://wa.me/525587654321?text=")

        # Record social touchpoint with explicit confirmation
        msg_res = await service.record_or_send_social_message(
            company_id=company.id,
            channel="WHATSAPP",
            message_text=wa["text"],
            recipient_identifier="525587654321",
            explicit_user_confirmed=True
        )
        assert msg_res["success"] is True
        assert msg_res["status"] == "SENT"
        assert msg_res["sales_stage"] == "CONTACTED"
