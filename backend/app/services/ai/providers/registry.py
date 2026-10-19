from typing import Dict
from app.services.ai.providers.base import AIExtractionProvider

class AIProviderRegistry:
    _providers: Dict[str, AIExtractionProvider] = {}

    @classmethod
    def register(cls, name: str, provider: AIExtractionProvider):
        cls._providers[name.lower()] = provider

    @classmethod
    def get_provider(cls, name: str) -> AIExtractionProvider:
        return cls._providers.get(name.lower())

registry = AIProviderRegistry()
