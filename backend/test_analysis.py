import asyncio
from app.services.crawler.client import CrawlerClient
from app.services.intelligence.extractor import WebsiteExtractor

async def main():
    crawler = CrawlerClient()
    extractor = WebsiteExtractor()
    
    url = "https://example.com"
    robots_status, robots_content, allowed = await crawler.fetch_robots_txt(url)
    print("Robots:", robots_status)
    
    page = await crawler.fetch_page(url)
    print("Page status:", page["status"])
    if page.get("html"):
        meta = extractor.extract_metadata(page["html"], url)
        print("Meta Title:", meta["title"])
        
        tech = extractor.detect_technologies(page["html"], page["headers"])
        print("Tech:", tech)

asyncio.run(main())
