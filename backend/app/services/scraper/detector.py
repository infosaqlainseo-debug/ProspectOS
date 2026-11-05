import re
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
import httpx
from urllib.parse import urljoin, urlparse

from app.core.security import validate_target_url
from app.services.scraper.cleaner import clean_and_validate_record

logger = logging.getLogger(__name__)

# Heuristic selectors for common repeating containers
CANDIDATE_CONTAINER_SELECTORS = [
    # Class-based listings
    ".card", ".listing-item", ".business-card", ".result-item", ".directory-item",
    ".company-card", ".vendor-card", ".product-item", ".search-result", ".profile-card",
    ".post-item", ".item-card", ".grid-item", ".store-item",
    # Semantic elements
    "article", "tbody tr", ".table tbody tr", "ul.results > li", "ul.listings > li",
    "div[data-testid*='card']", "div[data-testid*='result']", "div[itemtype*='Organization']",
    "div[itemtype*='LocalBusiness']", "div[itemtype*='Product']"
]

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"(\+?[\d\s\-\(\)\.]{8,20})")

async def detect_website_structure(url: str, html_override: Optional[str] = None) -> Dict[str, Any]:
    """
    Inspects target URL or provided HTML, identifies repeated structures,
    detects extractable fields, pagination, and generates an executable workflow.
    """
    is_safe, valid_url_or_err, _ = validate_target_url(url)
    if not is_safe and not html_override:
        return {
            "success": False,
            "error": valid_url_or_err,
            "target_url": url,
            "detected_container": None,
            "detected_fields": [],
            "pagination": None,
            "sample_records": [],
            "workflow_config": {}
        }

    target_url = valid_url_or_err
    html_content = html_override or ""
    http_status = 200

    if not html_content:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 ProspectOS-Scraper/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=headers, verify=False) as client:
                res = await client.get(target_url)
                http_status = res.status_code
                if res.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Target website returned HTTP {res.status_code}",
                        "target_url": target_url,
                        "detected_container": None,
                        "detected_fields": [],
                        "pagination": None,
                        "sample_records": [],
                        "workflow_config": {}
                    }
                html_content = res.text
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch webpage: {str(e)}",
                "target_url": target_url,
                "detected_container": None,
                "detected_fields": [],
                "pagination": None,
                "sample_records": [],
                "workflow_config": {}
            }

    soup = BeautifulSoup(html_content, "lxml")
    
    # 1. Page Metadata
    page_title = soup.title.string.strip() if soup.title and soup.title.string else ""
    meta_desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
    meta_description = meta_desc_tag["content"].strip() if meta_desc_tag and meta_desc_tag.get("content") else ""

    # 2. Find Repeating Container
    best_container = None
    best_count = 0
    candidate_elements = []

    # Check candidates
    for selector in CANDIDATE_CONTAINER_SELECTORS:
        matches = soup.select(selector)
        if len(matches) >= 2 and len(matches) > best_count:
            best_container = selector
            best_count = len(matches)
            candidate_elements = matches

    # Fallback: scan for repeated class patterns on divs or lis if no specific candidate matched
    if not best_container or best_count < 2:
        class_counts = {}
        for tag in soup.find_all(["div", "li", "section", "article"]):
            classes = tag.get("class")
            if classes:
                key = "." + ".".join(classes[:2])
                class_counts[key] = class_counts.get(key, 0) + 1
        
        # Sort classes by frequency, prefer between 3 and 100 items (not body wrappers)
        viable_classes = [(c, cnt) for c, cnt in class_counts.items() if 2 <= cnt <= 100]
        viable_classes.sort(key=lambda x: x[1], reverse=True)
        if viable_classes:
            best_container = viable_classes[0][0]
            candidate_elements = soup.select(best_container)
            best_count = len(candidate_elements)
        else:
            best_container = "body"
            candidate_elements = [soup.body] if soup.body else []
            best_count = 1

    # 3. Detect Fields inside the container
    detected_fields = []
    
    sample_el = candidate_elements[0] if candidate_elements else soup

    # A. Name / Title
    name_el = sample_el.select_one("h1, h2, h3, h4, .title, .name, [class*='name'], [class*='title'], strong")
    if name_el:
        tag_name = name_el.name
        classes = ".".join(name_el.get("class", []))
        sel = f"{tag_name}.{classes}" if classes else tag_name
        detected_fields.append({
            "name": "company_name",
            "label": "Company / Business Name",
            "selector": sel,
            "type": "text",
            "attribute": "text",
            "confidence": 0.95,
            "sample_value": name_el.get_text(strip=True)[:100]
        })
    else:
        detected_fields.append({
            "name": "company_name",
            "label": "Company / Business Name",
            "selector": "h2, h3, .title",
            "type": "text",
            "attribute": "text",
            "confidence": 0.50,
            "sample_value": page_title
        })

    # B. Link / Website
    link_el = sample_el.select_one("a[href]")
    if link_el:
        detected_fields.append({
            "name": "website",
            "label": "Website / Link URL",
            "selector": "a",
            "type": "link",
            "attribute": "href",
            "confidence": 0.90,
            "sample_value": urljoin(target_url, link_el.get("href", ""))
        })

    # C. Phone Number
    phone_el = sample_el.select_one("a[href^='tel:'], [class*='phone'], [class*='tel']")
    phone_sample = ""
    if phone_el:
        phone_sample = phone_el.get_text(strip=True) or phone_el.get("href", "").replace("tel:", "")
        detected_fields.append({
            "name": "phone",
            "label": "Phone Number",
            "selector": "a[href^='tel:'], [class*='phone'], [class*='tel']",
            "type": "text",
            "attribute": "text",
            "confidence": 0.85,
            "sample_value": phone_sample
        })
    else:
        # Check text regex
        text_match = PHONE_REGEX.search(sample_el.get_text())
        if text_match:
            detected_fields.append({
                "name": "phone",
                "label": "Phone Number",
                "selector": ":text-regex",
                "type": "text",
                "attribute": "text",
                "confidence": 0.70,
                "sample_value": text_match.group(1).strip()
            })

    # D. Email Address
    email_el = sample_el.select_one("a[href^='mailto:'], [class*='email'], [class*='mail']")
    if email_el:
        email_val = email_el.get_text(strip=True) or email_el.get("href", "").replace("mailto:", "").split("?")[0]
        detected_fields.append({
            "name": "email",
            "label": "Email Address",
            "selector": "a[href^='mailto:'], [class*='email']",
            "type": "text",
            "attribute": "text",
            "confidence": 0.88,
            "sample_value": email_val
        })
    else:
        m = EMAIL_REGEX.search(sample_el.get_text())
        if m:
            detected_fields.append({
                "name": "email",
                "label": "Email Address",
                "selector": ":text-regex",
                "type": "text",
                "attribute": "text",
                "confidence": 0.75,
                "sample_value": m.group(0).strip()
            })

    # E. Address / Location
    addr_el = sample_el.select_one("address, [class*='address'], [class*='location'], [class*='city'], .geo")
    if addr_el:
        detected_fields.append({
            "name": "address",
            "label": "Address / Location",
            "selector": "address, [class*='address'], [class*='location']",
            "type": "text",
            "attribute": "text",
            "confidence": 0.80,
            "sample_value": addr_el.get_text(strip=True)[:120]
        })

    # F. Category / Industry / Tag
    cat_el = sample_el.select_one("[class*='category'], [class*='badge'], [class*='tag'], [class*='industry']")
    if cat_el:
        detected_fields.append({
            "name": "category",
            "label": "Category / Industry",
            "selector": "[class*='category'], [class*='badge'], [class*='tag']",
            "type": "text",
            "attribute": "text",
            "confidence": 0.75,
            "sample_value": cat_el.get_text(strip=True)
        })

    # G. Description / Summary
    desc_el = sample_el.select_one("p, .desc, .description, .summary, [class*='bio']")
    if desc_el:
        detected_fields.append({
            "name": "description",
            "label": "Description",
            "selector": "p, .desc, .summary",
            "type": "text",
            "attribute": "text",
            "confidence": 0.80,
            "sample_value": desc_el.get_text(strip=True)[:180]
        })

    # H. Image URL
    img_el = sample_el.select_one("img[src]")
    if img_el:
        detected_fields.append({
            "name": "image_url",
            "label": "Image URL",
            "selector": "img",
            "type": "image",
            "attribute": "src",
            "confidence": 0.85,
            "sample_value": urljoin(target_url, img_el.get("src", ""))
        })

    # 4. Detect Pagination Pattern
    pagination_info = None
    next_btn = soup.select_one("a[rel='next'], .pagination .next, a:-soup-contains('Next'), a:-soup-contains('»'), [aria-label*='Next']")
    if next_btn and next_btn.get("href"):
        pagination_info = {
            "type": "NEXT_BUTTON",
            "selector": "a[rel='next'], .pagination .next, [aria-label*='Next']",
            "next_url": urljoin(target_url, next_btn["href"]),
            "max_pages": 5
        }
    else:
        # Check for query pattern like ?page=1 or /p/1
        if "page=" in target_url or "/p/" in target_url:
            pagination_info = {
                "type": "URL_PATTERN",
                "pattern": re.sub(r"page=\d+", "page={page}", target_url),
                "start_page": 1,
                "max_pages": 5
            }

    # 5. Extract Sample Preview Records (up to 5 items)
    sample_records = []
    for item_el in candidate_elements[:5]:
        rec = {}
        for f in detected_fields:
            fname = f["name"]
            fsel = f["selector"]
            ftype = f["type"]
            fattr = f["attribute"]
            
            sub_el = item_el.select_one(fsel) if fsel != ":text-regex" else item_el
            if sub_el:
                if ftype == "link" or fattr == "href":
                    val = urljoin(target_url, sub_el.get("href", ""))
                elif ftype == "image" or fattr == "src":
                    val = urljoin(target_url, sub_el.get("src", ""))
                elif fattr != "text" and sub_el.get(fattr):
                    val = sub_el.get(fattr)
                else:
                    val = sub_el.get_text(strip=True)
            else:
                val = ""
            rec[fname] = val
        
        rec["source_url"] = target_url
        cleaned_rec = clean_and_validate_record(rec)
        sample_records.append(cleaned_rec)

    # 6. Generate Standard Workflow Configuration
    workflow_config = {
        "start_url": target_url,
        "container_selector": best_container,
        "fields": detected_fields,
        "pagination": pagination_info,
        "rate_limit_delay_ms": 1000,
        "max_pages": 3,
        "max_records": 50,
        "steps": [
            {
                "id": "step_1",
                "type": "open_url",
                "name": "Navigate to Target Page",
                "params": {"url": target_url}
            },
            {
                "id": "step_2",
                "type": "loop_elements",
                "name": f"Loop Repeated Container ({best_container})",
                "params": {"container_selector": best_container}
            },
            {
                "id": "step_3",
                "type": "extract_fields",
                "name": "Extract Item Fields",
                "params": {"fields": detected_fields}
            },
            {
                "id": "step_4",
                "type": "clean_data",
                "name": "Normalize & Validate Data",
                "params": {"trim": True, "normalize_urls": True, "validate_contacts": True}
            },
            {
                "id": "step_5",
                "type": "save_results",
                "name": "Store Extracted Records",
                "params": {"deduplicate": True}
            }
        ]
    }

    return {
        "success": True,
        "target_url": target_url,
        "page_title": page_title,
        "meta_description": meta_description,
        "detected_container": best_container,
        "elements_found": best_count,
        "detected_fields": detected_fields,
        "pagination": pagination_info,
        "sample_records": sample_records,
        "workflow_config": workflow_config
    }
