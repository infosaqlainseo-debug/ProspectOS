import pytest
import os
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.security import validate_target_url, generate_api_key, hash_api_key
from app.services.scraper.cleaner import (
    clean_and_validate_record,
    normalize_url,
    normalize_phone,
    validate_email,
    compute_record_hash
)
from app.services.scraper.detector import detect_website_structure
from app.services.scraper.templates import get_all_templates, get_template_by_id
from app.services.scraper.engine import ScraperEngine
from app.services.scraper.exporter import create_export
from app.services.scraper.scheduler import calculate_next_run
from datetime import datetime, timezone

HTML_TEST_FIXTURE = """
<!DOCTYPE html>
<html>
<head><title>Top Mexican E-Commerce Brands Directory</title></head>
<body>
  <h1>Directory of E-Commerce Businesses in Mexico</h1>
  <div class="directory-list">
    <div class="business-card">
      <h3 class="title">Gaia Design</h3>
      <a class="website" href="https://www.gaiadesign.com.mx?utm_source=test&fbclid=123">Visit Website</a>
      <p class="desc">Modern furniture and home decor online store in Mexico.</p>
      <span class="phone">+52 55 5351 3803</span>
      <span class="email">contacto@gaiadesign.com.mx</span>
      <span class="address">Polanco, CDMX, Mexico</span>
      <span class="badge">E-commerce / Home</span>
    </div>
    <div class="business-card">
      <h3 class="title">Luuna Colchones</h3>
      <a class="website" href="https://luuna.mx">Visit Website</a>
      <p class="desc">Memory foam mattresses and sleep accessories direct to consumer.</p>
      <span class="phone">+52 55 4164 0533</span>
      <span class="email">hola@luuna.mx</span>
      <span class="address">Roma Norte, CDMX, Mexico</span>
      <span class="badge">E-commerce / D2C</span>
    </div>
  </div>
</body>
</html>
"""

# ----------------- 1. SSRF SECURITY TESTS -----------------

def test_ssrf_protection_blocks_internal_and_metadata():
    # Loopback
    is_safe, msg, _ = validate_target_url("http://127.0.0.1:8080/admin")
    assert not is_safe
    assert "forbidden" in msg.lower() or "blocked" in msg.lower()

    # Cloud metadata
    is_safe, msg, _ = validate_target_url("http://169.254.169.254/latest/meta-data/")
    assert not is_safe

    is_safe, msg, _ = validate_target_url("http://metadata.google.internal/computeMetadata/v1/")
    assert not is_safe

    # Localhost
    is_safe, msg, _ = validate_target_url("http://localhost:3000/internal")
    assert not is_safe

    # Invalid scheme
    is_safe, msg, _ = validate_target_url("ftp://ftp.example.com")
    assert not is_safe

    # Public safe URL
    is_safe, safe_url, ip = validate_target_url("https://example.com")
    assert is_safe
    assert safe_url == "https://example.com"
    assert ip is not None


# ----------------- 2. DATA CLEANING & NORMALIZATION -----------------

def test_data_cleaning_and_normalization():
    # URL normalization & tracking param removal
    norm_url, domain = normalize_url("https://www.gaiadesign.com.mx/products?utm_source=newsletter&fbclid=abc")
    assert "utm_source" not in norm_url
    assert "fbclid" not in norm_url
    assert domain == "gaiadesign.com.mx"

    # Phone normalization
    phone, is_valid = normalize_phone("+52 (55) 5351-3803")
    assert is_valid
    assert "+52" in phone
    assert len(phone) >= 10

    # Email validation
    email, is_valid = validate_email("contacto@gaiadesign.com.mx")
    assert is_valid
    assert email == "contacto@gaiadesign.com.mx"

    # Invalid email
    _, is_invalid = validate_email("invalid-email-no-at")
    assert not is_invalid

    # Quality scoring
    raw = {
        "company_name": "  Gaia Design  ",
        "website": "https://gaiadesign.com.mx",
        "email": "contacto@gaiadesign.com.mx",
        "phone": "+525553513803",
        "address": "Mexico City, Mexico"
    }
    cleaned = clean_and_validate_record(raw)
    assert cleaned["company_name"] == "Gaia Design"
    assert cleaned["validation_status"] == "VALID"
    assert cleaned["quality_score"] >= 80.0
    assert cleaned["quality_status"] == "HIGH"
    assert len(cleaned["record_hash"]) == 64


# ----------------- 3. AUTO-DETECTION & ENGINE -----------------

@pytest.mark.asyncio
async def test_auto_detection_and_extraction():
    detected = await detect_website_structure("https://directory-sample.com", html_override=HTML_TEST_FIXTURE)
    assert detected["success"] is True
    assert detected["detected_container"] == ".business-card"
    assert len(detected["detected_fields"]) >= 4
    assert len(detected["sample_records"]) == 2

    # Check field names
    field_names = [f["name"] for f in detected["detected_fields"]]
    assert "company_name" in field_names
    assert "website" in field_names

    first = detected["sample_records"][0]
    assert first["company_name"] == "Gaia Design"
    assert first["domain"] == "gaiadesign.com.mx"


# ----------------- 4. TEMPLATE LIBRARY -----------------

def test_templates_completeness():
    templates = get_all_templates()
    assert len(templates) == 12, f"Expected 12 templates, got {len(templates)}"

    for t in templates:
        assert "id" in t
        assert "name" in t
        assert "description" in t
        assert "data_source" in t
        assert "input_parameters" in t
        assert "output_fields" in t
        assert "example_output" in t
        assert len(t["output_fields"]) >= 3


# ----------------- 5. EXPORT FORMATS -----------------

def test_multi_format_exports():
    records = [
        {
            "company_name": "Kavak Mexico",
            "website": "https://www.kavak.com/mx",
            "domain": "kavak.com",
            "industry": "Automotive E-commerce",
            "country": "Mexico",
            "city": "Mexico City",
            "email": "ventas@kavak.com",
            "phone": "+525550000000",
            "quality_score": 95.0,
            "quality_status": "HIGH",
            "validation_status": "VALID",
            "source_url": "https://kavak.com",
            "discovery_source": "SCRAPER",
            "created_at": datetime.now(timezone.utc)
        }
    ]

    for fmt in ["CSV", "XLSX", "JSON", "HTML", "XML"]:
        fp, size, download_url = create_export(records, fmt)
        assert os.path.exists(fp)
        assert size > 0
        assert download_url.startswith("/api/scraper/export/download/")
        # Clean up test file
        try:
            os.remove(fp)
        except OSError:
            pass


# ----------------- 6. SCHEDULER INCREMENTAL -----------------

def test_scheduler_incremental_calculations():
    now = datetime(2026, 10, 31, 12, 0, 0, tzinfo=timezone.utc)
    hourly = calculate_next_run("HOURLY", from_time=now)
    assert hourly.hour == 13

    daily = calculate_next_run("DAILY", from_time=now)
    assert daily.day == 1 and daily.month == 11 # Next day

    weekly = calculate_next_run("WEEKLY", from_time=now)
    assert weekly.day == 7 and weekly.month == 11

    none_run = calculate_next_run("NONE", from_time=now)
    assert none_run is None


# ----------------- 7. API END-TO-END INTEGRATION -----------------

@pytest.mark.asyncio
async def test_api_endpoints_e2e():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Overview
        r = await client.get("/api/scraper/overview")
        assert r.status_code == 200
        assert "metrics" in r.json()

        # Templates
        r = await client.get("/api/scraper/templates")
        assert r.status_code == 200
        assert len(r.json()["templates"]) == 12

        # Create Task
        r = await client.post("/api/scraper/tasks", json={
            "name": "Integration Test Task",
            "target_url": "https://example.com/listings",
            "task_type": "CUSTOM",
            "workflow_config": {
                "container_selector": ".card",
                "fields": [{"name": "company_name", "selector": "h3", "type": "text"}]
            }
        })
        assert r.status_code == 201
        task_id = r.json()["task"]["id"]

        # Get Task
        r = await client.get(f"/api/scraper/tasks/{task_id}")
        assert r.status_code == 200
        assert r.json()["name"] == "Integration Test Task"

        # List Tasks
        r = await client.get("/api/scraper/tasks")
        assert r.status_code == 200
        assert r.json()["total"] >= 1

        # API Keys
        r = await client.post("/api/scraper/api-keys", json={"name": "Test Key", "rate_limit_rpm": 60})
        assert r.status_code == 201
        key_id = r.json()["id"]

        r = await client.delete(f"/api/scraper/api-keys/{key_id}")
        assert r.status_code == 200

        # Delete Task
        r = await client.delete(f"/api/scraper/tasks/{task_id}")
        assert r.status_code == 200

