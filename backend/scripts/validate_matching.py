import asyncio
import uuid
from sqlalchemy import select
from app.db.session import async_session_maker
from app.models import Company, CampaignProfile, MatchingRun, MatchResult, PublisherRecord
from app.services.matching.engine import MatchingEngine

async def main():
    async with async_session_maker() as session:
        # 1. Create a Prospect for validation
        suffix = uuid.uuid4().hex[:8]
        comp = Company(
            canonical_domain=f"real-prospect-{suffix}.com", 
            company_name="Tech Marketing Inc",
            industry="Technology",
            country="United States"
        )
        session.add(comp)
        await session.commit()
        await session.refresh(comp)
        
        # 2. Create Campaign Profile
        profile = CampaignProfile(
            company_id=comp.id,
            target_industry="Technology",
            target_geography="Global",
            max_budget=200.0
        )
        session.add(profile)
        await session.commit()
        
        print(f"Created Prospect: {comp.company_name} (ID: {comp.id})")
        print(f"Campaign Profile Target: {profile.target_industry}, Budget: ${profile.max_budget}")
        
        # 3. Run matching engine against real database inventory
        engine = MatchingEngine(session)
        run = await engine.run_matching(comp.id)
        
        print(f"\n--- MATCHING RUN RESULT ---")
        print(f"Run ID: {run.id}")
        print(f"Status: {run.status}")
        print(f"Total Eligible Inventory: {run.total_eligible}")
        print(f"Total Excluded (e.g. Budget > $200): {run.total_excluded}")
        
        # 4. Fetch Top 10 results
        results = await session.execute(
            select(MatchResult, PublisherRecord.publisher_name, Company.canonical_domain)
            .join(PublisherRecord, PublisherRecord.id == MatchResult.publisher_id)
            .join(Company, Company.id == PublisherRecord.company_id)
            .where(MatchResult.matching_run_id == run.id)
            .order_by(MatchResult.rank.asc())
            .limit(10)
        )
        
        print(f"\n--- TOP 10 MATCHED PUBLISHERS ---")
        for idx, (res, pub_name, domain) in enumerate(results):
            print(f"{idx+1}. {pub_name or domain} (Score: {res.overall_score:.1f})")
            print(f"    Topical: {res.component_scores['topical_relevance']:.1f}, "
                  f"Quality: {res.component_scores['publisher_quality']:.1f}, "
                  f"Price Fit: {res.component_scores['price_fit']:.1f}")
            for reason in res.reasons:
                print(f"    - {reason['evidence']}")
            for warning in res.warnings:
                print(f"    * WARNING: {warning}")
            print()

if __name__ == "__main__":
    asyncio.run(main())
