import os
import json
import re
import logging
from typing import Optional
from pydantic import ValidationError

import anthropic
from anthropic import AsyncAnthropic, AuthenticationError, RateLimitError, APIError

from app.services.ai.providers.base import AIExtractionProvider, ProviderExtractionResponse
from app.schemas.ai_extraction import AIExtractionResult
from app.core.config import settings

logger = logging.getLogger(__name__)

PROMPT_VERSION = "v1.1.0"

# Active, supported models in the Anthropic Claude product catalog
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-5-5"

CURRENT_SUPPORTED_ANTHROPIC_MODELS = [
    "claude-sonnet-5-5",  # Flagship: Optimal combination of speed and intelligence ($2.00 / $10.00 per MTok)
    "claude-haiku-5-5",   # High-volume, low-latency data extraction ($0.10 / $0.50 per MTok)
    "claude-opus-5-5",    # Deep long-running agentic tasks ($15.00 / $75.00 per MTok)
    "claude-fable-5-1",   # Complex multi-step reasoning ($3.00 / $15.00 per MTok)
]

# Known retired model IDs that have reached End-of-Life (EOL)
RETIRED_ANTHROPIC_MODELS = {
    # Claude 3.5 series (Retired)
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-20240620",
    "claude-3-5-sonnet",
    "claude-3-5-sonnet-latest",
    "claude-3-5-haiku-20241022",
    "claude-3-5-haiku",
    "claude-3-5-haiku-latest",
    # Claude 3 series (Retired)
    "claude-3-opus-20240229",
    "claude-3-opus",
    "claude-3-opus-latest",
    "claude-3-sonnet-20240229",
    "claude-3-sonnet",
    "claude-3-haiku-20240307",
    "claude-3-haiku",
    # Claude 4.0 / 3.7 retired snapshots
    "claude-3-7-sonnet-20250219",
    "claude-3-7-sonnet",
    "claude-sonnet-4-20250514",
    "claude-opus-4-20250514",
}


def sanitize_error_message(error_str: str) -> str:
    """Mask any API keys or credential patterns that may inadvertently appear in raw error strings."""
    if not error_str:
        return ""
    # Mask Anthropic key pattern
    sanitized = re.sub(r'sk-ant-[a-zA-Z0-9_\-]+', '[REDACTED_API_KEY]', error_str)
    # Mask generic authorization bearer tokens
    sanitized = re.sub(r'Bearer\s+[a-zA-Z0-9_\-\.]+', 'Bearer [REDACTED]', sanitized)
    return sanitized


def calculate_anthropic_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate approximate USD cost for Anthropic API token usage based on official pricing."""
    m = model_name.lower()
    if "haiku-5" in m or "5-5-haiku" in m:
        # Claude Haiku 5.5: $0.10 / 1M input, $0.50 / 1M output
        rate_in, rate_out = 0.10 / 1_000_000, 0.50 / 1_000_000
    elif "opus-5" in m or "5-5-opus" in m:
        # Claude Opus 5.5: $15.00 / 1M input, $75.00 / 1M output
        rate_in, rate_out = 15.00 / 1_000_000, 75.00 / 1_000_000
    elif "fable" in m:
        # Claude Fable 5.1: $3.00 / 1M input, $15.00 / 1M output
        rate_in, rate_out = 3.00 / 1_000_000, 15.00 / 1_000_000
    elif "3-5-haiku" in m:
        rate_in, rate_out = 0.80 / 1_000_000, 4.00 / 1_000_000
    elif "3-opus" in m:
        rate_in, rate_out = 15.00 / 1_000_000, 75.00 / 1_000_000
    else:
        # Claude Sonnet 5.5 (default): $2.00 / 1M input, $10.00 / 1M output
        rate_in, rate_out = 2.00 / 1_000_000, 10.00 / 1_000_000
    return round((input_tokens * rate_in) + (output_tokens * rate_out), 6)


class AnthropicProvider(AIExtractionProvider):
    provider_name = "Anthropic"
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = (
                os.getenv("ANTHROPIC_API_KEY")
                or getattr(settings, "ANTHROPIC_API_KEY", None)
                or getattr(settings, "LLM_API_KEY", None)
                or os.getenv("LLM_API_KEY")
                or ""
            )

        if model is not None:
            self.model = model
        else:
            self.model = (
                os.getenv("ANTHROPIC_MODEL")
                or getattr(settings, "ANTHROPIC_MODEL", None)
                or DEFAULT_ANTHROPIC_MODEL
            )

    def _get_client(self) -> AsyncAnthropic:
        return AsyncAnthropic(api_key=self.api_key, timeout=60.0)

    async def extract_company_attributes(self, evidence_text: str, schema_version: str = "v1") -> ProviderExtractionResponse:
        if not self.api_key or not self.api_key.strip():
            return ProviderExtractionResponse(
                provider_name=self.provider_name,
                model_name=self.model,
                prompt_version=PROMPT_VERSION,
                error="PROVIDER_NOT_CONFIGURED"
            )

        # Check for deprecated / retired model identifiers to avoid silent failure or guaranteed 400/404 errors
        if self.model in RETIRED_ANTHROPIC_MODELS:
            return ProviderExtractionResponse(
                provider_name=self.provider_name,
                model_name=self.model,
                prompt_version=PROMPT_VERSION,
                error=(
                    f"RETIRED_MODEL_ERROR: Model '{self.model}' is retired by Anthropic. "
                    f"Please update ANTHROPIC_MODEL to an active model (recommended: '{DEFAULT_ANTHROPIC_MODEL}' or 'claude-haiku-5-5')."
                )
            )

        system_prompt = (
            "You are a strict, objective AI data extractor. Your goal is to extract company attributes based ONLY on the provided evidence. "
            "Never invent, infer, or hallucinate attributes. "
            "If the evidence does not clearly support an attribute, omit it (leave it null/None). "
            "Every extracted attribute MUST include the exact text snippet from the evidence that supports it, and a confidence score (0.0 to 1.0). "
            "Call the `extract_company_attributes` tool to return the structured attributes matching the schema."
        )

        tool_schema = AIExtractionResult.model_json_schema()
        tool_definition = {
            "name": "extract_company_attributes",
            "description": "Extract structured company attributes supported strictly by evidence.",
            "input_schema": tool_schema
        }

        try:
            client = self._get_client()
            response = await client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=system_prompt,
                tools=[tool_definition],
                # tool_choice auto avoids conflicts with reasoning / thinking blocks across modern Claude 5.x models
                tool_choice={"type": "auto"},
                messages=[
                    {"role": "user", "content": f"Extract structured attributes from this evidence:\n\n{evidence_text}"}
                ]
            )

            # Extract usage metrics
            input_tokens = getattr(response.usage, "input_tokens", 0)
            output_tokens = getattr(response.usage, "output_tokens", 0)
            total_tokens = input_tokens + output_tokens
            estimated_cost = calculate_anthropic_cost(self.model, input_tokens, output_tokens)

            # Find tool use or fallback to JSON text block (skipping thinking blocks)
            parsed_payload = None
            raw_response_str = None

            for block in response.content:
                block_type = getattr(block, "type", None)
                if block_type == "tool_use" and getattr(block, "name", None) == "extract_company_attributes":
                    parsed_payload = getattr(block, "input", None)
                    raw_response_str = json.dumps(parsed_payload)
                    break
                elif block_type == "text":
                    raw_text = getattr(block, "text", "").strip()
                    if raw_text:
                        raw_response_str = raw_text

            if parsed_payload is None and raw_response_str:
                # Fallback: attempt to parse JSON from text block if tool was returned in text
                raw_text = raw_response_str
                try:
                    if "```json" in raw_text:
                        raw_text = raw_text.split("```json", 1)[1].split("```", 1)[0].strip()
                    elif "```" in raw_text:
                        raw_text = raw_text.split("```", 1)[1].split("```", 1)[0].strip()
                    parsed_payload = json.loads(raw_text)
                except json.JSONDecodeError:
                    pass

            if parsed_payload is None:
                return ProviderExtractionResponse(
                    provider_name=self.provider_name,
                    model_name=self.model,
                    prompt_version=PROMPT_VERSION,
                    error="VALIDATION_ERROR: Model returned no structured tool output or valid JSON block.",
                    total_tokens=total_tokens,
                    estimated_cost=estimated_cost,
                    raw_response=raw_response_str
                )

            try:
                # Support nested under `attributes` or flat dict
                if isinstance(parsed_payload, dict) and "attributes" not in parsed_payload:
                    parsed_payload = {"attributes": parsed_payload}

                result = AIExtractionResult.model_validate(parsed_payload)

                return ProviderExtractionResponse(
                    provider_name=self.provider_name,
                    model_name=self.model,
                    prompt_version=PROMPT_VERSION,
                    result=result,
                    total_tokens=total_tokens,
                    estimated_cost=estimated_cost,
                    raw_response=raw_response_str
                )
            except (ValidationError, json.JSONDecodeError) as e:
                return ProviderExtractionResponse(
                    provider_name=self.provider_name,
                    model_name=self.model,
                    prompt_version=PROMPT_VERSION,
                    error=f"VALIDATION_ERROR: {sanitize_error_message(str(e))}",
                    total_tokens=total_tokens,
                    estimated_cost=estimated_cost,
                    raw_response=raw_response_str
                )

        except AuthenticationError as e:
            return ProviderExtractionResponse(
                provider_name=self.provider_name,
                model_name=self.model,
                prompt_version=PROMPT_VERSION,
                error=f"AUTHENTICATION_FAILED: {sanitize_error_message(str(e))}"
            )
        except RateLimitError as e:
            return ProviderExtractionResponse(
                provider_name=self.provider_name,
                model_name=self.model,
                prompt_version=PROMPT_VERSION,
                error=f"RATE_LIMITED: {sanitize_error_message(str(e))}"
            )
        except APIError as e:
            return ProviderExtractionResponse(
                provider_name=self.provider_name,
                model_name=self.model,
                prompt_version=PROMPT_VERSION,
                error=f"PROVIDER_ERROR: {sanitize_error_message(str(e))}"
            )
        except Exception as e:
            sanitized_msg = sanitize_error_message(str(e))
            logger.error(f"Unexpected error in AnthropicProvider: {sanitized_msg}")
            return ProviderExtractionResponse(
                provider_name=self.provider_name,
                model_name=self.model,
                prompt_version=PROMPT_VERSION,
                error=f"PROVIDER_ERROR: {sanitized_msg}"
            )
