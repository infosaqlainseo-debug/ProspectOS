from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Generic, TypeVar
from app.schemas.enums import CompanySize, CompanyType

T = TypeVar('T')

class AIEvidence(BaseModel, Generic[T]):
    value: T = Field(description="The extracted value.")
    evidence_text: Optional[str] = Field(default=None, description="The exact quote or snippet of text that supports this value.")
    source_url: Optional[str] = Field(default=None, description="The URL of the page where the evidence was found.")
    confidence: Optional[float] = Field(default=None, description="Confidence score between 0.0 and 1.0 that this value is supported by the evidence.")

class AICompanyAttributes(BaseModel):
    primary_industry: Optional[AIEvidence[str]] = Field(default=None, description="The main industry the company operates in.")
    secondary_industries: Optional[AIEvidence[str]] = Field(default=None, description="A list of secondary industries (extracted as a comma-separated string).")
    company_type: Optional[AIEvidence[CompanyType]] = Field(default=None, description="The type of company.")
    business_model: Optional[AIEvidence[str]] = Field(default=None, description="The primary business model (e.g. Subscription, Perpetual).")
    is_b2b: Optional[AIEvidence[bool]] = Field(default=None, description="True if business-to-business.")
    is_b2c: Optional[AIEvidence[bool]] = Field(default=None, description="True if business-to-consumer.")
    company_size: Optional[AIEvidence[CompanySize]] = Field(default=None, description="The size enum of the company.")
    products: Optional[AIEvidence[str]] = Field(default=None, description="Key products offered (comma-separated string).")
    services: Optional[AIEvidence[str]] = Field(default=None, description="Key services offered (comma-separated string).")
    target_market: Optional[AIEvidence[str]] = Field(default=None, description="The target market or industry.")
    business_description: Optional[AIEvidence[str]] = Field(default=None, description="A concise description of what the business does based on evidence.")
    headquarters_location: Optional[AIEvidence[str]] = Field(default=None, description="The location of headquarters (City, Country).")

class AIExtractionResult(BaseModel):
    attributes: AICompanyAttributes
