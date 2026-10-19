import asyncio
from typing import List, AsyncGenerator
from duckduckgo_search import AsyncDDGS
from app.schemas.discovery import DiscoveryRequest, DiscoveryResult
from app.services.discovery.base import DiscoveryProvider

class DuckDuckGoProvider(DiscoveryProvider):
    @property
    def source_name(self) -> str:
        return "DuckDuckGo Public Web Search"

    def _build_query(self, request: DiscoveryRequest) -> str:
        if request.query:
            return request.query
            
        parts = []
        if request.industry:
            parts.append(request.industry)
        if request.company_type:
            parts.append(request.company_type)
        parts.append("companies")
        
        location = []
        if request.city:
            location.append(request.city)
        if request.state:
            location.append(request.state)
        if request.country:
            location.append(request.country)
            
        if location:
            parts.append("in")
            parts.append(", ".join(location))
            
        return " ".join(parts)

    async def discover(self, request: DiscoveryRequest) -> AsyncGenerator[List[DiscoveryResult], None]:
        query = self._build_query(request)
        
        try:
            # AsyncDDGS allows async search
            results = await AsyncDDGS().text(query, max_results=request.target_count * 2)
            
            # Since DDG returns web pages, we convert them to basic discovery results
            # The pipeline will normalize URLs and deduplicate.
            batch = []
            for r in results:
                # Basic heuristic: title is often "Company Name - ... " or just "Company Name"
                # We'll just pass the title and let normalization handle the URL
                title = r.get("title", "")
                url = r.get("href", "")
                
                # Split title by common separators
                company_name = title.split("|")[0].split("-")[0].strip()
                if not company_name:
                    company_name = title
                    
                result = DiscoveryResult(
                    company_name=company_name,
                    website_url=url,
                    source_url="https://duckduckgo.com/?q=" + query.replace(" ", "+"),
                    source_name=self.source_name,
                    discovery_method="public_web_search",
                    confidence=0.5 # Web search is low confidence for exact company record
                )
                batch.append(result)
                
                if len(batch) >= 10:
                    yield batch
                    batch = []
                    await asyncio.sleep(0.5) # Rate limiting
                    
            if batch:
                yield batch
                
        except Exception as e:
            # Log error (in a real system we'd use proper logging)
            print(f"DuckDuckGo search error: {e}")
            yield []
