import re
import json
import logging
from typing import Optional, Dict, Any
from app.schemas.discovery import StructuredSearchConfig, NLQueryParseResponse
from app.core.config import settings

logger = logging.getLogger(__name__)

COUNTRY_SYNONYMS = {
    "mexico": "Mexico",
    "mx": "Mexico",
    "usa": "United States",
    "united states": "United States",
    "us": "United States",
    "america": "United States",
    "uk": "United Kingdom",
    "united kingdom": "United Kingdom",
    "britain": "United Kingdom",
    "uae": "United Arab Emirates",
    "united arab emirates": "United Arab Emirates",
    "dubai": "United Arab Emirates",
    "canada": "Canada",
    "germany": "Germany",
    "spain": "Spain",
    "france": "France",
    "australia": "Australia",
    "brazil": "Brazil",
    "colombia": "Colombia"
}

INDUSTRY_PATTERNS = [
    (r"\b(e-?commerce|online stores?|retail|dtc)\b", "E-commerce / Online Retail"),
    (r"\b(saas|software|b2b software|cloud apps?)\b", "SaaS / B2B Software"),
    (r"\b(fintech|finance|banking|crypto|payments)\b", "Fintech & Financial Services"),
    (r"\b(health(care)?|medical|clinic|pharma|wellness)\b", "Healthcare & Medical"),
    (r"\b(real estate|property|realtor|realty)\b", "Real Estate & Commercial"),
    (r"\b(legal|law firm|attorney|lawyer)\b", "Legal & Professional Services"),
    (r"\b(agency|marketing|consulting|digital marketing)\b", "Agency & Professional Services"),
    (r"\b(local service|plumb|roof|contractor|hvac)\b", "Local Service Businesses"),
    (r"\b(travel|tourism|hospitality|hotel)\b", "Travel & Hospitality"),
    (r"\b(education|edtech|course|university|school)\b", "Education & EdTech"),
]

SERVICE_PATTERNS = [
    (r"\btechnical seo\b", "Technical SEO"),
    (r"\blink building\b", "Link Building"),
    (r"\bdigital pr\b", "Digital PR"),
    (r"\bcontent strategy\b", "Content Strategy"),
    (r"\blocal seo\b", "Local SEO"),
    (r"\bbacklinks?\b", "High-Authority Backlinks"),
    (r"\bwebsite audit\b", "Full Website Audit"),
]

def parse_with_heuristics(query: str) -> StructuredSearchConfig:
    q_lower = query.lower()
    
    # 1. Target Count (e.g. "Find 50 new companies", "get 25 leads", "100 prospects")
    count_match = re.search(r"\b(\d+)\s*(?:new\s*)?(?:companies|prospects|leads|websites|businesses|domains)\b", q_lower)
    if not count_match:
        count_match = re.search(r"\b(?:find|scrape|get|discover|collect)\s+(\d+)\b", q_lower)
    target_count = int(count_match.group(1)) if count_match else 50
    if target_count <= 0 or target_count > 1000:
        target_count = 50

    # 2. Country Detection
    detected_country: Optional[str] = None
    for token, official_name in COUNTRY_SYNONYMS.items():
        if re.search(rf"\b{re.escape(token)}\b", q_lower):
            detected_country = official_name
            break

    # 3. Industry Detection
    detected_industry: Optional[str] = None
    for pat, label in INDUSTRY_PATTERNS:
        if re.search(pat, q_lower):
            detected_industry = label
            break

    # 4. Desired Service Opportunities
    detected_services = []
    for pat, s_name in SERVICE_PATTERNS:
        if re.search(pat, q_lower):
            detected_services.append(s_name)
    desired_service_opportunity = ", ".join(detected_services) if detected_services else "Technical SEO, Link Building, and Digital PR"

    # 5. Weak SEO / Poor Organic Visibility -> Opportunity focus
    max_seo_score: Optional[float] = None
    if re.search(r"\b(weak|poor|low|bad|outdated|sub-par|lagging)\s+(?:seo|organic|visibility|traffic|rankings)\b", q_lower):
        max_seo_score = 65.0  # Means looking for high gap / weak baseline

    # 6. Exclusion Rules
    exclusions = []
    excl_match = re.search(r"\b(?:exclude|excluding|no|without)\s+([a-zA-Z0-9,\s]+?)(?:\.|$|and)", q_lower)
    if excl_match:
        raw_excl = excl_match.group(1).split(",")
        exclusions = [x.strip() for x in raw_excl if x.strip()]

    # 7. Summary
    summary_parts = [f"Discover {target_count} target companies"]
    if detected_country:
        summary_parts.append(f"in {detected_country}")
    if detected_industry:
        summary_parts.append(f"operating in the {detected_industry} sector")
    if max_seo_score:
        summary_parts.append("with low organic visibility / high SEO improvement potential")
    if desired_service_opportunity:
        summary_parts.append(f"targeting {desired_service_opportunity} for GrokxSEO services")

    interpreted_summary = " ".join(summary_parts) + "."

    return StructuredSearchConfig(
        raw_query=query,
        interpreted_summary=interpreted_summary,
        target_count=target_count,
        country=detected_country or "Mexico",
        industry=detected_industry or "E-commerce",
        business_type=detected_industry or "E-commerce",
        max_seo_score=max_seo_score or 65.0,
        desired_service_opportunity=desired_service_opportunity,
        source_preferences=["duckduckgo", "directory", "web_search"],
        exclusion_rules=exclusions,
        include_previously_discovered=False,
        min_data_quality="accessible_website",
        confidence_score=0.92
    )


async def parse_natural_language_query(query: str) -> NLQueryParseResponse:
    """Interprets a natural language prospecting instruction into a structured, editable search configuration."""
    if not query or len(query.strip()) < 3:
        raise ValueError("Search instruction is too short to interpret.")

    # Try Anthropic Claude if configured
    if settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY.startswith("sk-ant-"):
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            
            system_prompt = """You are an expert lead generation & SEO data architect for ProspectOS.
Your job is to parse natural-language search instructions into a structured JSON configuration.
Respond ONLY with valid JSON conforming to the following keys:
{
  "target_count": int,
  "country": str or null,
  "city": str or null,
  "industry": str or null,
  "company_size": str or null,
  "business_type": str or null,
  "min_seo_score": float or null,
  "max_seo_score": float or null,
  "desired_service_opportunity": str or null,
  "source_preferences": list of str,
  "exclusion_rules": list of str,
  "include_previously_discovered": bool,
  "min_data_quality": str,
  "interpreted_summary": str
}
Do not include markdown fences or explanations outside the JSON."""

            user_message = f"Instruction: {query}"
            
            resp = await client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=600,
                temperature=0.0,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )
            
            content_text = resp.content[0].text.strip()
            # Clean up potential markdown formatting
            if content_text.startswith("```"):
                lines = content_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                content_text = "\n".join(lines).strip()
                
            parsed = json.loads(content_text)
            
            config = StructuredSearchConfig(
                raw_query=query,
                interpreted_summary=parsed.get("interpreted_summary") or f"Discovered search criteria from instruction.",
                target_count=int(parsed.get("target_count") or 50),
                country=parsed.get("country"),
                city=parsed.get("city"),
                industry=parsed.get("industry"),
                company_size=parsed.get("company_size"),
                business_type=parsed.get("business_type"),
                min_seo_score=parsed.get("min_seo_score"),
                max_seo_score=parsed.get("max_seo_score"),
                desired_service_opportunity=parsed.get("desired_service_opportunity"),
                source_preferences=parsed.get("source_preferences") or ["duckduckgo", "directory"],
                exclusion_rules=parsed.get("exclusion_rules") or [],
                include_previously_discovered=bool(parsed.get("include_previously_discovered", False)),
                min_data_quality=parsed.get("min_data_quality") or "accessible_website",
                confidence_score=0.98
            )
            
            return NLQueryParseResponse(
                success=True,
                config=config,
                parsing_method="anthropic_claude"
            )
        except Exception as e:
            logger.warning(f"Claude NL parsing encountered error, falling back to heuristic parser: {e}")

    # Fallback to high-accuracy deterministic heuristic NLP parser
    config = parse_with_heuristics(query)
    return NLQueryParseResponse(
        success=True,
        config=config,
        parsing_method="rule_heuristic_engine"
    )
