import pytest
import uuid
import json
import httpx
import respx
from app.services.ai.providers.openai_adapter import OpenAIProvider

@pytest.mark.asyncio
async def test_openai_provider_valid_extraction():
    provider = OpenAIProvider()
    provider.api_key = "test_key"
    
    evidence = "Acme Corp is a B2B SaaS company that sells CRM software to medium businesses."
    
    mock_response = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "attributes": {
                        "primary_industry": {
                            "value": "Software",
                            "evidence_text": "sells CRM software",
                            "confidence": 0.95
                        },
                        "is_b2b": {
                            "value": True,
                            "evidence_text": "B2B SaaS company",
                            "confidence": 0.99
                        },
                        "company_size": {
                            "value": "MEDIUM",
                            "evidence_text": "medium businesses",
                            "confidence": 0.90
                        }
                    }
                })
            }
        }],
        "usage": {
            "total_tokens": 150,
            "prompt_tokens": 100,
            "completion_tokens": 50
        }
    }
    
    with respx.mock:
        respx.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(200, json=mock_response)
        )
        
        resp = await provider.extract_company_attributes(evidence)
        
        assert resp.error is None
        assert resp.result is not None
        assert resp.result.attributes.primary_industry.value == "Software"
        assert resp.result.attributes.is_b2b.value is True
        assert resp.result.attributes.company_size.value == "MEDIUM"
        assert resp.total_tokens == 150

@pytest.mark.asyncio
async def test_openai_provider_invalid_extraction():
    provider = OpenAIProvider()
    provider.api_key = "test_key"
    
    # Mocking hallucinated structure
    mock_response = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "attributes": {
                        "company_size": {
                            "value": "INVALID_ENUM_SIZE",
                            "evidence_text": "trust me bro",
                            "confidence": 1.0
                        }
                    }
                })
            }
        }],
        "usage": {"total_tokens": 10}
    }
    
    with respx.mock:
        respx.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(200, json=mock_response)
        )
        
        resp = await provider.extract_company_attributes("some text")
        
        assert resp.error is not None
        assert "VALIDATION_ERROR" in resp.error
