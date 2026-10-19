import os
import json
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import anthropic
from anthropic.types import Message, Usage, ToolUseBlock, TextBlock
from anthropic import AuthenticationError, RateLimitError

from app.services.ai.providers.anthropic_adapter import (
    AnthropicProvider,
    calculate_anthropic_cost,
    DEFAULT_ANTHROPIC_MODEL,
    CURRENT_SUPPORTED_ANTHROPIC_MODELS,
    RETIRED_ANTHROPIC_MODELS,
)
from app.services.ai.providers import registry
from app.services.ai.runner import AIExtractionRunner
from app.models import Company, Job, WebsiteScan, AIExtractionRun, AIObservation
from app.db.session import async_session_maker
from sqlalchemy import select


# =========================================================================
# MOCK-BASED UNIT TESTS (Run without live API key / no external network)
# =========================================================================

@pytest.mark.asyncio
async def test_anthropic_provider_unconfigured():
    """Verify provider returns PROVIDER_NOT_CONFIGURED safely without crash when API key is missing."""
    provider = AnthropicProvider(api_key="")
    resp = await provider.extract_company_attributes("Acme Corp is a B2B SaaS company.")
    
    assert resp.error == "PROVIDER_NOT_CONFIGURED"
    assert resp.provider_name == "Anthropic"
    assert resp.result is None


@pytest.mark.asyncio
async def test_anthropic_provider_retired_model_error():
    """Verify that attempting to use a retired model returns RETIRED_MODEL_ERROR and prevents failing calls."""
    provider = AnthropicProvider(api_key="test_key", model="claude-3-5-sonnet-20241022")
    resp = await provider.extract_company_attributes("Some company evidence text.")
    
    assert resp.error is not None
    assert "RETIRED_MODEL_ERROR" in resp.error
    assert "claude-3-5-sonnet-20241022" in resp.error
    assert resp.result is None


@pytest.mark.asyncio
async def test_anthropic_provider_tool_use_valid_extraction():
    """Verify structured output parsing from Anthropic tool use response with active model."""
    provider = AnthropicProvider(api_key="test_anthropic_key", model="claude-sonnet-5-5")
    
    mock_payload = {
        "attributes": {
            "primary_industry": {
                "value": "Enterprise Software",
                "evidence_text": "sells CRM software to enterprise companies",
                "source_url": "https://example.com/about",
                "confidence": 0.98
            },
            "is_b2b": {
                "value": True,
                "evidence_text": "B2B SaaS platform",
                "source_url": "https://example.com",
                "confidence": 0.99
            },
            "is_b2c": {
                "value": False,
                "evidence_text": "strictly business clients",
                "source_url": "https://example.com",
                "confidence": 0.95
            },
            "company_size": {
                "value": "MEDIUM",
                "evidence_text": "medium businesses",
                "source_url": "https://example.com",
                "confidence": 0.90
            },
            "business_description": {
                "value": "Acme delivers cloud CRM automation.",
                "evidence_text": "Acme delivers cloud CRM automation to medium businesses.",
                "source_url": "https://example.com",
                "confidence": 0.96
            }
        }
    }
    
    mock_message = Message(
        id="msg_test_123",
        content=[
            ToolUseBlock(
                id="toolu_test_1",
                name="extract_company_attributes",
                input=mock_payload,
                type="tool_use"
            )
        ],
        model="claude-sonnet-5-5",
        role="assistant",
        stop_reason="tool_use",
        stop_sequence=None,
        type="message",
        usage=Usage(input_tokens=150, output_tokens=85)
    )
    
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_message)
    
    with patch.object(provider, "_get_client", return_value=mock_client):
        resp = await provider.extract_company_attributes("Acme is a B2B SaaS platform.")
        
        assert resp.error is None
        assert resp.result is not None
        assert resp.result.attributes.primary_industry.value == "Enterprise Software"
        assert resp.result.attributes.is_b2b.value is True
        assert resp.result.attributes.is_b2c.value is False
        assert resp.result.attributes.company_size.value == "MEDIUM"
        assert resp.total_tokens == 235
        assert resp.estimated_cost > 0.0


@pytest.mark.asyncio
async def test_anthropic_provider_text_fallback_extraction():
    """Verify fallback parsing when Anthropic returns JSON in a markdown text block."""
    provider = AnthropicProvider(api_key="test_anthropic_key", model="claude-sonnet-5-5")
    
    json_text = json.dumps({
        "attributes": {
            "primary_industry": {
                "value": "Cybersecurity",
                "evidence_text": "leading provider of cloud cybersecurity",
                "confidence": 0.92
            },
            "is_b2b": {
                "value": True,
                "evidence_text": "enterprise security solutions",
                "confidence": 0.95
            }
        }
    })
    
    mock_message = Message(
        id="msg_test_text",
        content=[
            TextBlock(
                text=f"Here is the extraction:\n```json\n{json_text}\n```",
                type="text"
            )
        ],
        model="claude-sonnet-5-5",
        role="assistant",
        stop_reason="end_turn",
        stop_sequence=None,
        type="message",
        usage=Usage(input_tokens=120, output_tokens=60)
    )
    
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_message)
    
    with patch.object(provider, "_get_client", return_value=mock_client):
        resp = await provider.extract_company_attributes("Leading provider of cybersecurity.")
        
        assert resp.error is None
        assert resp.result is not None
        assert resp.result.attributes.primary_industry.value == "Cybersecurity"
        assert resp.result.attributes.is_b2b.value is True
        assert resp.total_tokens == 180


@pytest.mark.asyncio
async def test_anthropic_provider_schema_validation_error():
    """Verify validation errors are caught and surfaced safely when invalid schema is received."""
    provider = AnthropicProvider(api_key="test_anthropic_key", model="claude-sonnet-5-5")
    
    # Invalid enum value for company_size
    invalid_payload = {
        "attributes": {
            "company_size": {
                "value": "MEGA_CORPORATION_UNKNOWN",
                "evidence_text": "huge company",
                "confidence": 1.0
            }
        }
    }
    
    mock_message = Message(
        id="msg_test_invalid",
        content=[
            ToolUseBlock(
                id="toolu_test_inv",
                name="extract_company_attributes",
                input=invalid_payload,
                type="tool_use"
            )
        ],
        model="claude-sonnet-5-5",
        role="assistant",
        stop_reason="tool_use",
        stop_sequence=None,
        type="message",
        usage=Usage(input_tokens=50, output_tokens=30)
    )
    
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_message)
    
    with patch.object(provider, "_get_client", return_value=mock_client):
        resp = await provider.extract_company_attributes("Huge company.")
        
        assert resp.error is not None
        assert "VALIDATION_ERROR" in resp.error
        assert resp.result is None


@pytest.mark.asyncio
async def test_anthropic_provider_authentication_error():
    """Verify AuthenticationError is handled safely."""
    provider = AnthropicProvider(api_key="invalid_key", model="claude-sonnet-5-5")
    
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(
        side_effect=AuthenticationError(
            message="Invalid API Key",
            response=MagicMock(status_code=401, headers={}),
            body={"error": {"message": "Invalid API Key"}}
        )
    )
    
    with patch.object(provider, "_get_client", return_value=mock_client):
        resp = await provider.extract_company_attributes("Test evidence.")
        
        assert resp.error is not None
        assert "AUTHENTICATION_FAILED" in resp.error


@pytest.mark.asyncio
async def test_anthropic_provider_rate_limit_error():
    """Verify RateLimitError is handled safely."""
    provider = AnthropicProvider(api_key="test_key", model="claude-sonnet-5-5")
    
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(
        side_effect=RateLimitError(
            message="Rate limit exceeded",
            response=MagicMock(status_code=429, headers={}),
            body={"error": {"message": "Rate limit exceeded"}}
        )
    )
    
    with patch.object(provider, "_get_client", return_value=mock_client):
        resp = await provider.extract_company_attributes("Test evidence.")
        
        assert resp.error is not None
        assert "RATE_LIMITED" in resp.error


def test_registry_has_both_providers():
    """Ensure both OpenAI and Anthropic are registered without breaking existing providers."""
    openai_p = registry.get_provider("openai")
    anthropic_p = registry.get_provider("anthropic")
    
    assert openai_p is not None
    assert openai_p.provider_name == "OpenAI"
    
    assert anthropic_p is not None
    assert anthropic_p.provider_name == "Anthropic"


def test_calculate_anthropic_cost_accuracy():
    """Test cost calculation across active Claude 5.5 model family."""
    # Sonnet 5.5: $2.00 / 1M input, $10.00 / 1M output
    sonnet_cost = calculate_anthropic_cost("claude-sonnet-5-5", 1000, 500)
    # Haiku 5.5: $0.10 / 1M input, $0.50 / 1M output
    haiku_cost = calculate_anthropic_cost("claude-haiku-5-5", 1000, 500)
    
    assert sonnet_cost == round(1000 * 0.000002 + 500 * 0.000010, 6)
    assert haiku_cost == round(1000 * 0.00000010 + 500 * 0.00000050, 6)
    assert sonnet_cost > haiku_cost


@pytest.mark.asyncio
async def test_runner_persistence_with_anthropic():
    """Test end-to-end extraction and observation creation with Anthropic provider in AIExtractionRunner."""
    mock_company = Company(
        id=uuid.uuid4(),
        canonical_domain="anthropic-corp.com",
        company_name="Anthropic Test Corp",
        description="Leading AI infrastructure provider.",
        industry="Artificial Intelligence"
    )
    mock_scan = WebsiteScan(
        id=uuid.uuid4(),
        company_id=mock_company.id,
        url="https://anthropic-corp.com",
        title="Anthropic Test Corp | AI Solutions",
        meta_description="Enterprise B2B AI platform for data operations.",
        h1=["Enterprise AI Platform"],
        h2=["Built for B2B Teams"]
    )
    mock_run_record = AIExtractionRun(
        id=uuid.uuid4(),
        company_id=mock_company.id,
        job_id=uuid.uuid4(),
        provider="Anthropic",
        model="claude-sonnet-5-5",
        prompt_version="v1.1.0",
        schema_version="v1",
        status="RUNNING"
    )

    mock_session = AsyncMock()
    # Handle session.get calls
    def mock_get(model, obj_id):
        if model == Company:
            return mock_company
        if model == AIExtractionRun:
            return mock_run_record
        return None
    mock_session.get.side_effect = mock_get

    # Mock execute results: first for WebsiteScan, then for contradiction checks
    mock_result_scan = MagicMock()
    mock_result_scan.scalar_one_or_none.return_value = mock_scan

    mock_result_obs = MagicMock()
    mock_result_obs.scalar_one_or_none.return_value = None

    mock_session.execute.side_effect = [mock_result_scan, mock_result_obs, mock_result_obs, mock_result_obs]

    # Capture added objects
    added_objects = []
    def mock_add(obj):
        added_objects.append(obj)
    mock_session.add = MagicMock(side_effect=mock_add)

    # Mock async session maker
    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__.return_value = mock_session
    mock_session_maker.return_value.__aexit__.return_value = None

    # Mock the Anthropic extraction response
    mock_payload = {
        "attributes": {
            "primary_industry": {
                "value": "Artificial Intelligence",
                "evidence_text": "Enterprise B2B AI platform",
                "confidence": 0.97
            },
            "is_b2b": {
                "value": True,
                "evidence_text": "Built for B2B Teams",
                "confidence": 0.95
            }
        }
    }
    
    mock_message = Message(
        id="msg_runner_test",
        content=[
            ToolUseBlock(
                id="toolu_runner_1",
                name="extract_company_attributes",
                input=mock_payload,
                type="tool_use"
            )
        ],
        model="claude-sonnet-5-5",
        role="assistant",
        stop_reason="tool_use",
        stop_sequence=None,
        type="message",
        usage=Usage(input_tokens=200, output_tokens=100)
    )

    anthropic_provider = registry.get_provider("anthropic")
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_message)

    with patch("app.services.ai.runner.async_session_maker", mock_session_maker), \
         patch.object(anthropic_provider, "_get_client", return_value=mock_client), \
         patch.object(anthropic_provider, "api_key", "mock_key"):
        runner = AIExtractionRunner(job_id=str(mock_run_record.job_id), provider_name="anthropic")
        result = await runner.run_extraction(mock_company.id)
        
        assert result["status"] == "COMPLETED"
        assert result["observations_created"] == 2
        assert mock_run_record.status == "COMPLETED"
        assert mock_run_record.total_tokens == 300
        assert mock_run_record.estimated_cost is not None
        assert mock_session.commit.called

        # Verify AIObservation instances were persisted
        obs_added = [obj for obj in added_objects if isinstance(obj, AIObservation)]
        assert len(obs_added) == 2
        obs_map = {o.attribute_name: o for o in obs_added}
        assert "primary_industry" in obs_map
        assert obs_map["primary_industry"].attribute_value == "Artificial Intelligence"
        assert obs_map["primary_industry"].verification_status == "VERIFIED"
        assert "is_b2b" in obs_map
        assert obs_map["is_b2b"].attribute_value == "True"


# =========================================================================
# LIVE API TESTS (Requires real API credential; skipped if not configured)
# =========================================================================

from app.core.config import settings

@pytest.mark.asyncio
@pytest.mark.skipif(
    not (os.getenv("ANTHROPIC_API_KEY") or getattr(settings, "ANTHROPIC_API_KEY", None) or os.getenv("LLM_API_KEY")),
    reason="LIVE API TEST: Skipped because ANTHROPIC_API_KEY credential is not configured in environment."
)
async def test_anthropic_live_api_extraction():
    """LIVE API TEST: Tests actual connection to Anthropic Claude API using currently supported model."""
    api_key = os.getenv("ANTHROPIC_API_KEY") or getattr(settings, "ANTHROPIC_API_KEY", None) or os.getenv("LLM_API_KEY")
    provider = AnthropicProvider(api_key=api_key, model="claude-sonnet-5-5")
    
    evidence = (
        "Stripe is a financial infrastructure platform for businesses. "
        "Millions of companies from startups to Fortune 500s use Stripe’s software to accept payments, "
        "grow their revenue, and accelerate new business opportunities."
    )
    
    resp = await provider.extract_company_attributes(evidence)
    
    assert resp.error is None, f"Live Anthropic API request failed: {resp.error}"
    assert resp.result is not None
    assert resp.total_tokens > 0
    assert resp.estimated_cost > 0.0
    assert resp.result.attributes.is_b2b is not None
    assert resp.result.attributes.is_b2b.value is True
