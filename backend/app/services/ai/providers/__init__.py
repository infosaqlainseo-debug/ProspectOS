from app.services.ai.providers.registry import registry
from app.services.ai.providers.openai_adapter import OpenAIProvider
from app.services.ai.providers.anthropic_adapter import AnthropicProvider

registry.register("openai", OpenAIProvider())
registry.register("anthropic", AnthropicProvider())

__all__ = ["registry", "OpenAIProvider", "AnthropicProvider"]
