import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import httpx
from bs4 import BeautifulSoup

from app.core.security import validate_target_url
from app.services.scraper.cleaner import clean_and_validate_record
from app.services.scraper.detector import detect_website_structure

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 ProspectOS-Scraper/1.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1"
}

class ScraperEngine:
    def __init__(self, timeout_seconds: float = 20.0, rate_limit_delay_ms: int = 800):
        self.timeout_seconds = timeout_seconds
        self.rate_limit_delay_ms = rate_limit_delay_ms
        self.logs: List[Dict[str, Any]] = []

    def _log(self, level: str, message: str):
        now_str = datetime.now(timezone.utc).isoformat()
        self.logs.append({
            "timestamp": now_str,
            "level": level,
            "message": message
        })
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)

    async def check_robots_allowed(self, target_url: str) -> bool:
        """Checks target website's robots.txt directives safely."""
        parsed = urlparse(target_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        is_safe, _, _ = validate_target_url(robots_url)
        if not is_safe:
            return True # If robots URL fails SSRF, continue cautiously
            
        try:
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True, headers=DEFAULT_HEADERS, verify=False) as client:
                res = await client.get(robots_url)
                if res.status_code == 200:
                    rp = RobotFileParser()
                    rp.parse(res.text.splitlines())
                    allowed = rp.can_fetch(DEFAULT_HEADERS["User-Agent"], target_url)
                    if not allowed:
                        self._log("WARNING", f"Robots.txt for {parsed.netloc} disallows crawling '{target_url}' for standard agents.")
                    return allowed
        except Exception as e:
            self._log("INFO", f"Robots.txt check skipped for {parsed.netloc}: {e}")
        return True

    async def fetch_page(self, url: str) -> Tuple[int, str, Optional[str]]:
        """Safely fetches a single webpage. Returns (http_status, html_content, error_message)."""
        is_safe, safe_url, _ = validate_target_url(url)
        if not is_safe:
            self._log("ERROR", f"SSRF Protection blocked URL: {safe_url}")
            return 0, "", f"SSRF Blocked: {safe_url}"

        self._log("INFO", f"Navigating to: {safe_url}")
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                follow_redirects=True,
                headers=DEFAULT_HEADERS,
                verify=False
            ) as client:
                res = await client.get(safe_url)
                
                # Check for bot challenge or block
                if res.status_code == 403:
                    self._log("WARNING", f"HTTP 403 Forbidden received at {safe_url}. Access restricted by target site.")
                    return res.status_code, "", "Access Restricted (HTTP 403 Forbidden)"
                elif res.status_code == 429:
                    self._log("WARNING", f"HTTP 429 Rate Limited at {safe_url}.")
                    return res.status_code, "", "Rate Limited (HTTP 429)"
                elif res.status_code >= 500:
                    self._log("ERROR", f"Server error HTTP {res.status_code} at {safe_url}")
                    return res.status_code, "", f"Server Error (HTTP {res.status_code})"
                
                return res.status_code, res.text, None
        except httpx.TimeoutException:
            self._log("ERROR", f"Request timed out connecting to {url}")
            return 0, "", "Connection Timeout"
        except Exception as e:
            self._log("ERROR", f"Connection error: {str(e)}")
            return 0, "", str(e)

    def extract_from_soup(
        self,
        soup: BeautifulSoup,
        current_url: str,
        workflow_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extracts items from BeautifulSoup DOM according to workflow configuration."""
        container_sel = workflow_config.get("container_selector")
        fields = workflow_config.get("fields") or []

        # If table extraction
        if workflow_config.get("extract_table_selector"):
            return self._extract_table(soup, current_url, workflow_config["extract_table_selector"])

        if not container_sel or container_sel == "auto":
            # Attempt auto detection on soup
            detected = detect_website_structure(current_url, html_override=str(soup))
            container_sel = detected.get("detected_container") or "body"
            if not fields:
                fields = detected.get("detected_fields") or []

        containers = soup.select(container_sel)
        self._log("INFO", f"Found {len(containers)} elements matching container '{container_sel}'")
        
        extracted_items = []
        for el in containers:
            item_raw = {}
            for f in fields:
                fname = f.get("name")
                fsel = f.get("selector")
                ftype = f.get("type", "text")
                fattr = f.get("attribute", "text")
                
                if not fname or not fsel:
                    continue

                target_sub = el.select_one(fsel) if fsel != ":text-regex" else el
                if target_sub:
                    if ftype == "link" or fattr == "href":
                        val = urljoin(current_url, target_sub.get("href", ""))
                    elif ftype == "image" or fattr == "src":
                        val = urljoin(current_url, target_sub.get("src", ""))
                    elif fattr != "text" and target_sub.get(fattr):
                        val = target_sub.get(fattr)
                    else:
                        val = target_sub.get_text(strip=True)
                else:
                    val = ""
                item_raw[fname] = val
                
            item_raw["source_url"] = current_url
            cleaned_rec = clean_and_validate_record(item_raw)
            extracted_items.append(cleaned_rec)

        return extracted_items

    def _extract_table(self, soup: BeautifulSoup, current_url: str, table_sel: str) -> List[Dict[str, Any]]:
        """Extracts HTML <table> elements into structured records."""
        table = soup.select_one(table_sel)
        if not table:
            return []
            
        headers = [th.get_text(strip=True) for th in table.select("thead th, tr th")]
        if not headers:
            # Fallback to column index
            first_row = table.select_one("tr")
            if first_row:
                headers = [f"column_{i+1}" for i in range(len(first_row.select("td, th")))]

        results = []
        for tr in table.select("tbody tr, tr"):
            tds = tr.select("td")
            if not tds:
                continue
            row_dict = {}
            for i, td in enumerate(tds):
                h = headers[i] if i < len(headers) else f"col_{i+1}"
                link = td.select_one("a[href]")
                if link and ("url" in h.lower() or "website" in h.lower()):
                    row_dict[h] = urljoin(current_url, link.get("href", ""))
                else:
                    row_dict[h] = td.get_text(strip=True)
            row_dict["source_url"] = current_url
            results.append(clean_and_validate_record(row_dict))
            
        return results

    async def execute_workflow(
        self,
        start_url: str,
        workflow_config: Dict[str, Any],
        max_records: int = 50,
        max_pages: int = 3,
        cancellation_token: Optional[asyncio.Event] = None
    ) -> Dict[str, Any]:
        """
        Executes a complete extraction workflow with pagination, rate limiting,
        data cleaning, and progress tracking.
        """
        start_time = time.time()
        self._log("INFO", f"Starting scraper workflow execution for: {start_url}")
        
        all_records: List[Dict[str, Any]] = []
        seen_hashes = set()
        current_url = start_url
        page_count = 0
        duplicate_count = 0

        # Check robots.txt
        await self.check_robots_allowed(start_url)

        pagination_cfg = workflow_config.get("pagination") or {}
        max_p = pagination_cfg.get("max_pages") or max_pages

        while current_url and page_count < max_p and len(all_records) < max_records:
            if cancellation_token and cancellation_token.is_set():
                self._log("WARNING", "Execution cancelled by user request.")
                break

            page_count += 1
            self._log("INFO", f"Fetching Page {page_count}: {current_url}")
            status, html, err = await self.fetch_page(current_url)
            
            if err or status != 200 or not html:
                self._log("ERROR", f"Page fetch failed: {err or f'HTTP {status}'}")
                break

            soup = BeautifulSoup(html, "lxml")
            extracted = self.extract_from_soup(soup, current_url, workflow_config)

            page_new_records = 0
            for r in extracted:
                h = r["record_hash"]
                if h in seen_hashes:
                    duplicate_count += 1
                    r["is_duplicate"] = True
                else:
                    seen_hashes.add(h)
                    r["is_duplicate"] = False
                    all_records.append(r)
                    page_new_records += 1
                    if len(all_records) >= max_records:
                        break

            self._log("INFO", f"Page {page_count} processed: {page_new_records} new records added ({duplicate_count} duplicates skipped)")

            if len(all_records) >= max_records:
                self._log("INFO", f"Reached target record limit of {max_records}.")
                break

            # Find next page
            next_url = None
            if pagination_cfg.get("type") == "NEXT_BUTTON" and pagination_cfg.get("selector"):
                next_btn = soup.select_one(pagination_cfg["selector"])
                if next_btn and next_btn.get("href"):
                    next_url = urljoin(current_url, next_btn["href"])
                    if next_url == current_url:
                        next_url = None
            elif pagination_cfg.get("type") == "URL_PATTERN" and pagination_cfg.get("pattern"):
                next_url = pagination_cfg["pattern"].replace("{page}", str(page_count + 1))
            
            if next_url:
                current_url = next_url
                # Polite rate limit delay
                await asyncio.sleep(self.rate_limit_delay_ms / 1000.0)
            else:
                self._log("INFO", "No further pagination link detected. Extraction finished.")
                break

        duration = round(time.time() - start_time, 2)
        valid_records = [r for r in all_records if r.get("validation_status") == "VALID"]
        
        self._log("INFO", f"Workflow execution completed in {duration}s. Extracted {len(all_records)} records, {duplicate_count} duplicates.")

        return {
            "success": len(all_records) > 0 or page_count > 0,
            "duration_seconds": duration,
            "pages_crawled": page_count,
            "total_extracted": len(all_records),
            "valid_records_count": len(valid_records),
            "duplicate_records_count": duplicate_count,
            "records": all_records,
            "logs": self.logs
        }

