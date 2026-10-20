from typing import List, Dict, Optional
from app.schemas.discovery import ScrapingTemplate

PROSPECTING_TEMPLATES: List[ScrapingTemplate] = [
    ScrapingTemplate(
        id="mexico-ecommerce",
        name="Mexico — Low-SEO E-commerce Companies",
        category="E-commerce",
        country="Mexico",
        industry="E-commerce / Retail",
        description="Discovers online retail and e-commerce companies across Mexico with low organic search visibility and high demand for technical SEO, link building, and GrokxSEO publisher backlink placements.",
        target_count=50,
        default_sources=["DuckDuckGo Public Web Search", "Public Business Listings"],
        extraction_fields=["Company Name", "Canonical Domain", "Industry", "Title/Meta Tags", "Technical SEO Gaps", "Public Contact Info", "WhatsApp Contact", "Social Profiles"],
        validation_rules=["Domain RFC 3986 Normalization", "HTTP/HTTPS Status Check", "Cloudflare WAF Classification", "Canonical Deduplication"],
        desired_services=["Technical SEO", "Link Building", "Digital PR"],
        min_seo_opportunity_score=50.0,
        config_requirements={"DuckDuckGo Search": "Available", "Crawler Engine": "Active", "Ahrefs API": "Configured"},
        is_available=True
    ),
    ScrapingTemplate(
        id="mexico-local-services",
        name="Mexico — Local Service Businesses",
        category="Local Services",
        country="Mexico",
        industry="Local Services / Healthcare / Legal",
        description="Targets professional and commercial service businesses in Mexico City, Guadalajara, and Monterrey with accessible websites needing on-page optimization and citation authority.",
        target_count=30,
        default_sources=["DuckDuckGo Public Web Search", "Public Business Listings"],
        extraction_fields=["Company Name", "Website URL", "City/State", "Telephone/WhatsApp", "Contact Page", "Page Speed & Meta Findings"],
        validation_rules=["Live Website Verification", "No Anti-Bot Bypass", "Deduplication vs CRM"],
        desired_services=["Local SEO", "Technical SEO", "On-Page Optimization"],
        min_seo_opportunity_score=45.0,
        config_requirements={"Crawler Engine": "Active"},
        is_available=True
    ),
    ScrapingTemplate(
        id="usa-ecommerce-seo",
        name="USA — E-commerce SEO Opportunities",
        category="E-commerce",
        country="United States",
        industry="E-commerce / Consumer Brands",
        description="Identifies US consumer e-commerce brands and online stores with organic ranking deficits that benefit from GrokxSEO authority backlinks and publisher inventory.",
        target_count=50,
        default_sources=["DuckDuckGo Public Web Search", "Public Web Sitemaps"],
        extraction_fields=["Company Name", "Domain", "Organic Traffic Profile", "Referring Domains Gap", "Authority Gap", "Contact Page"],
        validation_rules=["HTTP Validation", "No Synthetic Metrics", "Ahrefs Domain Rating Check"],
        desired_services=["Link Building", "Content Strategy", "Digital PR"],
        min_seo_opportunity_score=55.0,
        config_requirements={"Ahrefs API": "Configured", "Crawler Engine": "Active"},
        is_available=True
    ),
    ScrapingTemplate(
        id="uae-business-audit",
        name="UAE — Business Website SEO Audit Prospects",
        category="Commercial B2B",
        country="United Arab Emirates",
        industry="Commercial Real Estate & B2B Services",
        description="Targets commercial enterprise, real estate, and trade websites in Dubai and Abu Dhabi for comprehensive technical SEO audits and high-authority PR placements.",
        target_count=25,
        default_sources=["DuckDuckGo Public Web Search", "Public Directories"],
        extraction_fields=["Company Name", "Domain", "Indexability", "Robots/Sitemap Status", "WhatsApp Click-to-Chat", "LinkedIn/Instagram"],
        validation_rules=["HTTPS Verification", "403 Access Restriction Logging"],
        desired_services=["Technical SEO", "High-Authority PR Placements"],
        min_seo_opportunity_score=50.0,
        config_requirements={"Crawler Engine": "Active"},
        is_available=True
    ),
    ScrapingTemplate(
        id="uk-digital-pr",
        name="UK — Digital PR and Link-Building Prospects",
        category="Tech & Media",
        country="United Kingdom",
        industry="Fintech, SaaS & Tech Startups",
        description="Discovers UK-based technology and fintech brands with strong market validation but underdeveloped backlink profiles, ready for GrokxSEO Digital PR campaigns.",
        target_count=40,
        default_sources=["DuckDuckGo Public Web Search", "Public Listings"],
        extraction_fields=["Company Name", "Domain", "Topical Gaps", "Press/Newsroom Page", "Editorial Backlink Opportunities"],
        validation_rules=["Live Domain Check", "Evidence Grounding"],
        desired_services=["Digital PR", "Link Building", "Publisher Placement"],
        min_seo_opportunity_score=60.0,
        config_requirements={"Ahrefs API": "Configured", "Claude Extraction": "Active"},
        is_available=True
    ),
    ScrapingTemplate(
        id="agency-saas",
        name="Agency and SaaS Website Prospects",
        category="B2B Software",
        country="Global / Multi-Region",
        industry="SaaS & Digital Agencies",
        description="Scrapes B2B software vendors and creative agencies seeking recurring monthly backlink acquisition, white-label SEO execution, and content expansion.",
        target_count=50,
        default_sources=["DuckDuckGo Public Web Search", "Public Directories"],
        extraction_fields=["Company Name", "Domain", "SaaS Category", "Technical SEO Gaps", "Public Business Email", "Social Profile Links"],
        validation_rules=["Domain Normalization", "CRM Deduplication"],
        desired_services=["Full-Service SEO", "Link Building"],
        min_seo_opportunity_score=50.0,
        config_requirements={"Crawler Engine": "Active"},
        is_available=True
    )
]

def get_template_by_id(template_id: str) -> Optional[ScrapingTemplate]:
    for t in PROSPECTING_TEMPLATES:
        if t.id == template_id:
            return t
    return None
