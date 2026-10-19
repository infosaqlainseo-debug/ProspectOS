import os
import json
from pydantic import ValidationError
from app.services.ai.providers.base import AIExtractionProvider, ProviderExtractionResponse
from app.schemas.ai_extraction import AIExtractionResult, AICompanyAttributes
import httpx
from app.core.config import settings

PROMPT_VERSION = "v1.0.0"

class OpenAIProvider(AIExtractionProvider):
    provider_name = "OpenAI"
    model = "gpt-4o-mini"
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY") or getattr(settings, "LLM_API_KEY", None) or ""
        
    async def extract_company_attributes(self, evidence_text: str, schema_version: str = "v1") -> ProviderExtractionResponse:
        if not self.api_key:
            return ProviderExtractionResponse(
                provider_name=self.provider_name,
                model_name=self.model,
                prompt_version=PROMPT_VERSION,
                error="PROVIDER_NOT_CONFIGURED"
            )
            
        system_prompt = (
            "You are a strict, objective AI data extractor. Your goal is to extract company attributes based ONLY on the provided evidence. "
            "Never invent, infer, or hallucinate attributes. "
            "If the evidence does not clearly support an attribute, omit it (leave it null/None). "
            "Every extracted attribute MUST include the exact text snippet from the evidence that supports it, and a confidence score (0.0 to 1.0). "
            "Your output must be a valid JSON object matching the AIExtractionResult schema."
        )
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Extract structured attributes from this evidence:\n\n{evidence_text}"}
                        ],
                        # We use simple JSON mode to force it to return valid json, though function calling/structured outputs is better.
                        "response_format": {"type": "json_object"}
                    }
                )
                
                resp.raise_for_status()
                data = resp.json()
                
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                total_tokens = usage.get("total_tokens", 0)
                
                # Approximate cost for 4o-mini (e.g. $0.00015 / 1k input, $0.0006 / 1k output) -> roughly just store 0
                estimated_cost = (usage.get("prompt_tokens", 0) * 0.00015 + usage.get("completion_tokens", 0) * 0.0006) / 1000
                
                try:
                    parsed_json = json.loads(content)
                    # Support both nested under `attributes` or flat
                    if "attributes" not in parsed_json:
                        parsed_json = {"attributes": parsed_json}
                    
                    result = AIExtractionResult.model_validate(parsed_json)
                    
                    return ProviderExtractionResponse(
                        provider_name=self.provider_name,
                        model_name=self.model,
                        prompt_version=PROMPT_VERSION,
                        result=result,
                        total_tokens=total_tokens,
                        estimated_cost=estimated_cost,
                        raw_response=content
                    )
                except (ValidationError, json.JSONDecodeError) as e:
                    return ProviderExtractionResponse(
                        provider_name=self.provider_name,
                        model_name=self.model,
                        prompt_version=PROMPT_VERSION,
                        error=f"VALIDATION_ERROR: {str(e)}",
                        total_tokens=total_tokens,
                        estimated_cost=estimated_cost,
                        raw_response=content
                    )
                    
        except Exception as e:
            return ProviderExtractionResponse(
                provider_name=self.provider_name,
                model_name=self.model,
                prompt_version=PROMPT_VERSION,
                error=f"PROVIDER_ERROR: {str(e)}"
            )
