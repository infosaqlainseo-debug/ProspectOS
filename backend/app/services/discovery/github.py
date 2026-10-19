import aiohttp
import asyncio
from typing import List, AsyncGenerator
from app.schemas.discovery import DiscoveryRequest, DiscoveryResult
from app.services.discovery.base import DiscoveryProvider

class GitHubOrgProvider(DiscoveryProvider):
    @property
    def source_name(self) -> str:
        return "GitHub Organizations API"

    def _build_query(self, request: DiscoveryRequest) -> str:
        parts = ["type:org"]
        
        # We can use country, state, or city for location
        locations = []
        if request.city:
            locations.append(request.city)
        if request.state:
            locations.append(request.state)
        if request.country:
            locations.append(request.country)
            
        if locations:
            # Join by space, though GitHub only allows simple string in location field
            # We'll just take the most specific one or comma separated
            loc_str = ",".join(locations)
            parts.append(f"location:\"{loc_str}\"")
            
        if request.industry:
            parts.append(request.industry)
            
        if request.company_type:
            parts.append(request.company_type)
            
        if request.query:
            parts.append(request.query)
            
        return " ".join(parts)

    async def discover(self, request: DiscoveryRequest) -> AsyncGenerator[List[DiscoveryResult], None]:
        query = self._build_query(request)
        per_page = 30 # Max sensible for quick fetches
        page = 1
        found = 0
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ProspectOS-Discovery/1.0"
        }
        
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"https://api.github.com/search/users?q={query}&per_page={per_page}&page={page}"
                
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        break # Rate limit or error
                        
                    data = await response.json()
                    items = data.get("items", [])
                    
                    if not items:
                        break # No more results
                        
                    batch = []
                    # Fetch detailed org data to get the blog/website
                    for item in items:
                        org_url = item["url"]
                        async with session.get(org_url, headers=headers) as org_response:
                            if org_response.status == 200:
                                org_data = await org_response.json()
                                
                                name = org_data.get("name") or org_data.get("login")
                                website = org_data.get("blog")
                                location = org_data.get("location")
                                
                                # According to rules: Need website to be usable, though pipeline handles rejecting empty ones.
                                # Let's yield it and let pipeline handle validation
                                result = DiscoveryResult(
                                    company_name=name,
                                    website_url=website,
                                    location=location,
                                    industry=request.industry,
                                    source_url=org_data.get("html_url"),
                                    source_name=self.source_name,
                                    discovery_method="github_api_search",
                                    confidence=0.8
                                )
                                batch.append(result)
                                
                        await asyncio.sleep(0.1) # Be gentle on the API
                        
                    if batch:
                        yield batch
                        
                    if len(items) < per_page:
                        break # Last page
                        
                    page += 1
