import re
import hashlib
from typing import Dict, Any, Tuple
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import tldextract

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "msclkid", "ref", "source", "mc_cid", "mc_eid"
}

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_DIGITS_REGEX = re.compile(r"[^\d+]")

def normalize_whitespace(text: Any) -> str:
    if text is None:
        return ""
    s = str(text)
    # Collapse multiple whitespace/newlines
    return " ".join(s.split()).strip()

def normalize_url(url: Any) -> Tuple[str, str]:
    """Returns (normalized_url, canonical_domain)"""
    if not url:
        return "", ""
    u = str(url).strip()
    if not u:
        return "", ""
    if not u.startswith(("http://", "https://")):
        u = "https://" + u
    try:
        parsed = urlparse(u)
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            clean_host = netloc[4:]
        else:
            clean_host = netloc
        
        # Strip tracking query params
        query_params = parse_qsl(parsed.query)
        clean_params = [(k, v) for k, v in query_params if k.lower() not in TRACKING_PARAMS]
        clean_query = urlencode(clean_params)
        
        path = parsed.path
        if path.endswith("/") and len(path) > 1:
            path = path[:-1]
            
        norm_url = urlunparse((scheme, netloc, path, parsed.params, clean_query, ""))
        
        ext = tldextract.extract(clean_host)
        if ext.domain and ext.suffix:
            canonical_domain = f"{ext.domain}.{ext.suffix}".lower()
        else:
            canonical_domain = clean_host
            
        return norm_url, canonical_domain
    except Exception:
        return u, ""

def normalize_phone(phone: Any) -> Tuple[str, bool]:
    """Returns (normalized_phone, is_valid)"""
    if not phone:
        return "", False
    raw = str(phone).strip()
    # Remove junk characters except digits, +, -, (, ), space
    cleaned = PHONE_DIGITS_REGEX.sub("", raw)
    digits_only = re.sub(r"\D", "", cleaned)
    
    # Needs at least 7 digits to be considered a real phone number
    if len(digits_only) < 7 or len(digits_only) > 15:
        return raw, False
        
    # Format nicely
    if raw.startswith("+"):
        formatted = f"+{digits_only}"
    else:
        formatted = digits_only
        
    return formatted, True

def validate_email(email: Any) -> Tuple[str, bool]:
    """Returns (normalized_email, is_valid)"""
    if not email:
        return "", False
    clean = str(email).strip().lower()
    # Check mailto: prefix
    if clean.startswith("mailto:"):
        clean = clean[7:]
    clean = clean.split("?")[0].strip()
    
    if not clean or len(clean) > 254:
        return "", False
        
    is_valid = bool(EMAIL_REGEX.match(clean))
    return clean, is_valid

def compute_record_hash(record_data: Dict[str, Any]) -> str:
    """Computes a deterministic SHA-256 fingerprint for deduplication."""
    domain = (record_data.get("domain") or "").lower().strip()
    website = (record_data.get("website") or "").lower().strip()
    company_name = (
        record_data.get("company_name")
        or record_data.get("name")
        or record_data.get("title")
        or record_data.get("author")
        or ""
    ).lower().strip()
    text_sample = (
        record_data.get("quote_text")
        or record_data.get("description")
        or record_data.get("summary")
        or ""
    ).lower().strip()[:100]
    url = (record_data.get("source_url") or record_data.get("url") or "").lower().strip()
    
    key_components = f"{domain}|{website}|{company_name}|{text_sample}|{url}"
    return hashlib.sha256(key_components.encode("utf-8")).hexdigest()

def clean_and_validate_record(raw_item: Dict[str, Any], default_source: str = "SCRAPER") -> Dict[str, Any]:
    """
    Cleans, validates, and quality-scores an extracted record.
    Preserves raw_data intact and populates cleaned_data and lead fields.
    """
    cleaned: Dict[str, Any] = {}
    validation_details: Dict[str, Any] = {
        "passed_checks": [],
        "warnings": [],
        "errors": []
    }
    
    # 1. Company Name / Title
    raw_name = (
        raw_item.get("company_name")
        or raw_item.get("name")
        or raw_item.get("title")
        or raw_item.get("author")
        or ""
    )
    clean_name = normalize_whitespace(raw_name)
    cleaned["company_name"] = clean_name
    if clean_name:
        validation_details["passed_checks"].append("Company name present")
    else:
        validation_details["warnings"].append("Company name missing")

    # 2. Website & Domain
    raw_web = (
        raw_item.get("website")
        or raw_item.get("website_url")
        or raw_item.get("url")
        or raw_item.get("link")
        or raw_item.get("author_link")
        or ""
    )
    clean_web, domain = normalize_url(raw_web)
    cleaned["website"] = clean_web
    cleaned["domain"] = domain
    if clean_web:
        validation_details["passed_checks"].append(f"Valid website URL ({domain})")
    else:
        validation_details["warnings"].append("Website URL missing")

    # 3. Email
    raw_email = raw_item.get("email") or raw_item.get("public_email") or ""
    clean_email, is_email_valid = validate_email(raw_email)
    cleaned["email"] = clean_email
    if clean_email:
        if is_email_valid:
            validation_details["passed_checks"].append("Email valid")
        else:
            validation_details["warnings"].append(f"Email '{clean_email}' has irregular format")

    # 4. Phone
    raw_phone = raw_item.get("phone") or raw_item.get("phone_number") or ""
    clean_phone, is_phone_valid = normalize_phone(raw_phone)
    cleaned["phone"] = clean_phone
    if clean_phone:
        if is_phone_valid:
            validation_details["passed_checks"].append("Phone number valid")
        else:
            validation_details["warnings"].append("Phone number could not be validated to standard length")

    # 5. Address / Location
    raw_addr = raw_item.get("address") or raw_item.get("location") or ""
    clean_addr = normalize_whitespace(raw_addr)
    cleaned["address"] = clean_addr

    # 6. Industry & Category
    raw_ind = raw_item.get("industry") or ""
    raw_cat = raw_item.get("category") or raw_item.get("business_category") or ""
    cleaned["industry"] = normalize_whitespace(raw_ind)
    cleaned["category"] = normalize_whitespace(raw_cat)

    # 7. Country & City
    raw_country = raw_item.get("country") or ""
    raw_city = raw_item.get("city") or ""
    clean_country = normalize_whitespace(raw_country)
    clean_city = normalize_whitespace(raw_city)
    cleaned["country"] = clean_country
    cleaned["city"] = clean_city

    # 8. Description
    raw_desc = raw_item.get("description") or raw_item.get("summary") or ""
    cleaned["description"] = normalize_whitespace(raw_desc)

    # 9. Social Profiles
    social_profiles = raw_item.get("social_profiles") or {}
    if not isinstance(social_profiles, dict):
        social_profiles = {}
        
    for k in ["facebook", "instagram", "linkedin", "twitter", "whatsapp", "youtube"]:
        val = raw_item.get(f"{k}_url") or raw_item.get(k) or social_profiles.get(k)
        if val:
            clean_soc, _ = normalize_url(val)
            if clean_soc:
                social_profiles[k] = clean_soc
    cleaned["social_profiles"] = social_profiles

    # 10. Source URL & Provenance
    source_url = raw_item.get("source_url") or raw_item.get("page_url") or clean_web or ""
    cleaned["source_url"] = source_url
    cleaned["discovery_source"] = raw_item.get("discovery_source") or default_source

    # Compute Quality Score (0 - 100)
    score = 20.0 # Baseline
    if clean_name:
        score += 25.0
    if domain:
        score += 25.0
    if clean_email or clean_phone:
        score += 15.0
    if clean_addr or clean_city or clean_country:
        score += 10.0
    if social_profiles:
        score += 5.0
        
    quality_score = min(100.0, score)
    if quality_score >= 70.0:
        quality_status = "HIGH"
    elif quality_score >= 45.0:
        quality_status = "MEDIUM"
    else:
        quality_status = "LOW"

    # Validation Status
    if clean_name and (clean_web or domain):
        validation_status = "VALID"
    elif clean_name or clean_web:
        validation_status = "PARTIAL"
    else:
        validation_status = "FAILED"
        validation_details["errors"].append("Record lacks both identifying name and website.")

    rec_hash = compute_record_hash(cleaned)

    return {
        "record_hash": rec_hash,
        "raw_data": raw_item,
        "cleaned_data": cleaned,
        "company_name": clean_name or None,
        "website": clean_web or None,
        "domain": domain or None,
        "industry": cleaned["industry"] or None,
        "category": cleaned["category"] or None,
        "country": cleaned["country"] or None,
        "city": cleaned["city"] or None,
        "email": clean_email or None,
        "phone": clean_phone or None,
        "address": clean_addr or None,
        "description": cleaned["description"] or None,
        "social_profiles": social_profiles if social_profiles else None,
        "source_url": source_url or None,
        "discovery_source": cleaned["discovery_source"],
        "validation_status": validation_status,
        "quality_score": quality_score,
        "quality_status": quality_status,
        "validation_details": validation_details,
    }

