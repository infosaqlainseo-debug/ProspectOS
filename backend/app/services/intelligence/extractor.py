import re
import json
from bs4 import BeautifulSoup
from typing import Dict, Any, List
from urllib.parse import urlparse, urljoin

class WebsiteExtractor:
    """Extracts deterministic signals from HTML"""
    
    @staticmethod
    def extract_metadata(html: str, url: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, "lxml")
        
        # Basic HTML metadata
        title_tag = soup.find("title")
        title = title_tag.text.strip() if title_tag else None
        
        meta_desc_tag = soup.find("meta", attrs={"name": "description"})
        meta_description = meta_desc_tag.get("content", "").strip() if meta_desc_tag else None
        
        canonical_tag = soup.find("link", rel="canonical")
        canonical = canonical_tag.get("href", "").strip() if canonical_tag else None
        
        robots_tag = soup.find("meta", attrs={"name": "robots"})
        robots_meta = robots_tag.get("content", "").strip() if robots_tag else None
        
        viewport_tag = soup.find("meta", attrs={"name": "viewport"})
        viewport = viewport_tag.get("content", "").strip() if viewport_tag else None
        
        # Charset
        charset = None
        charset_tag = soup.find("meta", charset=True)
        if charset_tag:
            charset = charset_tag.get("charset")
            
        html_tag = soup.find("html")
        language = html_tag.get("lang") if html_tag else None
        
        # Headings
        h1s = [h.text.strip() for h in soup.find_all("h1") if h.text.strip()]
        h2s = [h.text.strip() for h in soup.find_all("h2") if h.text.strip()]
        
        # Open Graph
        open_graph = {}
        for og_tag in soup.find_all("meta", property=re.compile(r"^og:")):
            prop = og_tag.get("property")
            content = og_tag.get("content")
            if prop and content:
                open_graph[prop] = content
                
        # Twitter Card
        twitter_card = {}
        for tw_tag in soup.find_all("meta", attrs={"name": re.compile(r"^twitter:")}):
            name = tw_tag.get("name")
            content = tw_tag.get("content")
            if name and content:
                twitter_card[name] = content

        # Schema.org (JSON-LD)
        schemas = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                if script.string:
                    schemas.append(json.loads(script.string))
            except json.JSONDecodeError:
                pass

        return {
            "title": title,
            "meta_description": meta_description,
            "canonical_url": canonical,
            "robots_meta": robots_meta,
            "viewport": viewport,
            "language": language,
            "charset": charset,
            "h1": h1s,
            "h2": h2s,
            "open_graph": open_graph,
            "twitter_card": twitter_card,
            "schema_detected": schemas if schemas else None
        }

    @staticmethod
    def extract_social_links(html: str, base_url: str) -> List[Dict[str, str]]:
        soup = BeautifulSoup(html, "lxml")
        social_platforms = {
            "linkedin": r"linkedin\.com/(company|in)/",
            "facebook": r"facebook\.com/",
            "twitter": r"twitter\.com/|x\.com/",
            "instagram": r"instagram\.com/",
            "youtube": r"youtube\.com/|youtu\.be/",
            "tiktok": r"tiktok\.com/"
        }
        
        found = []
        seen = set()
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            # Skip empty or anchor links
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue
                
            absolute_url = urljoin(base_url, href)
            
            for platform, pattern in social_platforms.items():
                if re.search(pattern, absolute_url, re.IGNORECASE):
                    if absolute_url not in seen:
                        seen.add(absolute_url)
                        found.append({
                            "platform": platform,
                            "profile_url": absolute_url,
                            "source_url": base_url,
                            "verification_method": "HTML_LINK_EXTRACTION",
                            "confidence": 0.95
                        })
        return found
        
    @staticmethod
    def detect_technologies(html: str, headers: Dict[str, str]) -> Dict[str, Any]:
        technologies = {}
        soup = BeautifulSoup(html, "lxml")
        html_str = html.lower()
        
        # Very basic detection for phase 1.4
        if "wp-content" in html_str or "wp-includes" in html_str:
            technologies["WordPress"] = {"category": "CMS", "evidence": "wp-content detected"}
        if "cdn.shopify.com" in html_str:
            technologies["Shopify"] = {"category": "Ecommerce", "evidence": "cdn.shopify.com detected"}
        if "wix.com" in html_str or "wix-image" in html_str:
            technologies["Wix"] = {"category": "CMS", "evidence": "wix assets detected"}
        if 'id="__next"' in html_str:
            technologies["Next.js"] = {"category": "Framework", "evidence": "__next div detected"}
        if 'data-reactroot' in html_str:
            technologies["React"] = {"category": "Framework", "evidence": "data-reactroot detected"}
            
        header_str = str(headers).lower()
        if "cloudflare" in header_str:
            technologies["Cloudflare"] = {"category": "CDN", "evidence": "Cloudflare header"}
            
        return technologies if technologies else None
