from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.schemas.ai_extraction import AIExtractionResult

class ProviderExtractionResponse(BaseModel):
    provider_name: str
    model_name: str
    prompt_version: str
    result: Optional[AIExtractionResult] = None
    total_tokens: Optional[int] = None
    estimated_cost: Optional[float] = None
    error: Optional[str] = None
    raw_response: Optional[str] = None

class AIExtractionProvider(ABC):
    provider_name: str
    
    @abstractmethod
    async def extract_company_attributes(self, evidence_text: str, schema_version: str = "v1") -> ProviderExtractionResponse:
        """Extract structured company attributes from unstructured evidence text."""
        pass
