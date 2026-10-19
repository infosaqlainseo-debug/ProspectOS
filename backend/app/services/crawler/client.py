import httpx
import logging
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, Tuple
import asyncio
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)

class CrawlerClient:
    def __init__(self, timeout: int = 15, max_redirects: int = 5):
        self.timeout = timeout
        self.max_redirects = max_redirects
        self.headers = {
            "User-Agent": "ProspectOS-Crawler/1.0 (+https://prospectos.local/bot)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        
    async def fetch_robots_txt(self, base_url: str) -> Tuple[str, str, bool]:
        """Returns (status, content, allowed)"""
        robots_url = urljoin(base_url, "/robots.txt")
        status = "NOT_FOUND"
        content = ""
        allowed = True
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, headers=self.headers, verify=False) as client:
                response = await client.get(robots_url)
                if response.status_code == 200:
                    status = "FOUND"
                    content = response.text
                    try:
                        rp = RobotFileParser()
                        rp.parse(content.splitlines())
                        allowed = rp.can_fetch(self.headers["User-Agent"], base_url)
                    except Exception as parse_err:
                        logger.warning(f"Error parsing robots.txt for {base_url}: {parse_err}")
                        allowed = True
                elif response.status_code in (401, 403):
                    status = "FORBIDDEN"
                    allowed = True  # Standard crawl policy: 403 on robots.txt does not automatically forbid homepage unless homepage returns 403
                elif response.status_code == 404:
                    status = "NOT_FOUND"
                    allowed = True
                else:
                    status = f"HTTP_{response.status_code}"
                    allowed = True
        except Exception as e:
            status = f"ERROR: {str(e)}"
            allowed = True
            
        return status, content, allowed

    async def fetch_page(self, url: str) -> Dict[str, Any]:
        """Fetch a single HTML page with transparent access-restriction classification."""
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return {
                "url": url,
                "error": "Invalid scheme",
                "status": "FAILED",
                "is_accessible": False,
                "failure_reason": "INVALID_SCHEME",
                "http_status": None
            }
            
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers=self.headers,
                max_redirects=self.max_redirects,
                verify=False
            ) as client:
                response = await client.get(url)
                
                chain = [str(r.url) for r in response.history] if response.history else []
                is_accessible = response.status_code == 200
                failure_reason = None
                status = "COMPLETED" if is_accessible else "FAILED"
                
                server_header = (response.headers.get("server") or "").lower()
                cf_ray = response.headers.get("cf-ray")
                body_snippet = response.text[:1000].lower() if "text/html" in response.headers.get("content-type", "").lower() else ""

                if response.status_code == 403:
                    status = "ACCESS_RESTRICTED"
                    if "cloudflare" in server_header or cf_ray or "attention required! | cloudflare" in body_snippet or "just a moment..." in body_snippet:
                        failure_reason = "BOT_PROTECTION_CHALLENGE (Cloudflare WAF / Bot Management)"
                    elif "incapsula" in body_snippet or "imperva" in body_snippet:
                        failure_reason = "BOT_PROTECTION_CHALLENGE (Imperva / Incapsula WAF)"
                    elif "akamai" in body_snippet or "akamai" in server_header:
                        failure_reason = "BOT_PROTECTION_CHALLENGE (Akamai WAF)"
                    else:
                        failure_reason = "EXPLICIT_ACCESS_FORBIDDEN (HTTP 403 Forbidden)"
                elif response.status_code == 401:
                    status = "ACCESS_RESTRICTED"
                    failure_reason = "AUTHENTICATION_REQUIRED (HTTP 401 Unauthorized)"
                elif response.status_code == 429:
                    status = "RATE_LIMITED"
                    failure_reason = "RATE_LIMIT_EXCEEDED (HTTP 429 Too Many Requests)"
                elif response.status_code >= 500:
                    status = "SERVER_ERROR"
                    failure_reason = f"SERVER_ERROR (HTTP {response.status_code})"
                elif response.status_code != 200:
                    status = "FAILED"
                    failure_reason = f"HTTP_{response.status_code}"

                # Never treat block/challenge page HTML as legitimate site content
                valid_html = response.text if (is_accessible and "text/html" in response.headers.get("content-type", "").lower()) else ""
                
                return {
                    "url": url,
                    "final_url": str(response.url),
                    "http_status": response.status_code,
                    "is_accessible": is_accessible,
                    "failure_reason": failure_reason,
                    "response_time_ms": int(response.elapsed.total_seconds() * 1000),
                    "content_type": response.headers.get("content-type", ""),
                    "content_length": len(response.content),
                    "redirect_chain": chain,
                    "https_enabled": str(response.url).startswith("https"),
                    "html": valid_html,
                    "headers": dict(response.headers),
                    "status": status,
                    "error": f"HTTP {response.status_code}: {failure_reason}" if failure_reason else None
                }
        except httpx.TimeoutException:
            return {
                "url": url,
                "error": "Request timed out",
                "status": "TIMEOUT",
                "is_accessible": False,
                "failure_reason": "TIMEOUT",
                "http_status": None
            }
        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "status": "FAILED",
                "is_accessible": False,
                "failure_reason": f"CONNECTION_ERROR: {str(e)}",
                "http_status": None
            }

