import pytest
import uuid
from app.db.session import async_session_maker
from app.models import Company, GoogleDriveConnection, GoogleDriveSyncJob
from app.services.gdrive.service import GoogleDriveService, _encrypt_token, _decrypt_token

def test_token_encryption_roundtrip():
    token = "ya29.a0AfH6SM...test_token_secret"
    enc = _encrypt_token(token)
    assert enc != token
    dec = _decrypt_token(enc)
    assert dec == token

@pytest.mark.asyncio
async def test_gdrive_service_status_and_oauth_url():
    async with async_session_maker() as session:
        service = GoogleDriveService(session)
        status = await service.get_status()
        assert "is_connected" in status
        assert "selected_folder_path" in status
        assert "export_format" in status

        url = service.generate_auth_url(
            client_id="test_client_id.apps.googleusercontent.com",
            redirect_uri="http://localhost:3001/google-drive/callback"
        )
        assert "accounts.google.com/o/oauth2/v2/auth" in url
        assert "test_client_id" in url
        assert "scope=" in url

@pytest.mark.asyncio
async def test_gdrive_unconnected_sync_graceful_handling():
    async with async_session_maker() as session:
        # Create test prospect
        company = Company(
            company_name="Drive Test Brand",
            canonical_domain=f"drivetest-{uuid.uuid4().hex[:6]}.com",
            country="Mexico",
            industry="E-commerce",
            sales_stage="QUALIFIED"
        )
        session.add(company)
        await session.commit()
        await session.refresh(company)

        service = GoogleDriveService(session)
        # When unconnected, sync must return NOT_CONNECTED gracefully without crashing
        res = await service.sync_company_to_drive(company.id, sync_type="MANUAL")
        assert res["success"] is False
        assert res["status"] in ["NOT_CONNECTED", "AUTH_REQUIRED"]
        assert "job_id" in res

        # Verify job record was persisted
        job_id = uuid.UUID(res["job_id"])
        job = await session.get(GoogleDriveSyncJob, job_id)
        assert job is not None
        assert job.status == "FAILED"
        assert "Google Drive is not connected" in job.error_message
