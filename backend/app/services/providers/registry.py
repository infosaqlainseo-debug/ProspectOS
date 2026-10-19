from typing import Dict, Type
from app.services.providers.base import SEOProvider

class SEOProviderRegistry:
    _providers: Dict[str, SEOProvider] = {}

    @classmethod
    def register(cls, name: str, provider: SEOProvider):
        cls._providers[name.lower()] = provider

    @classmethod
    def get_provider(cls, name: str) -> SEOProvider:
        return cls._providers.get(name.lower())

    @classmethod
    def get_all_providers(cls) -> Dict[str, SEOProvider]:
        return cls._providers

registry = SEOProviderRegistry()
