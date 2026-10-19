import pytest
import uuid
from datetime import datetime, timezone, timedelta
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.main import app
from app.models import (
    Company,
    CRMDeal,
    OutreachCampaign,
    RevenueAnalyticsSnapshot
)
from app.schemas.analytics import (
    BENCHMARK_EXCHANGE_RATES_USD,
    RevenueFilterParams,
    SnapshotCreateRequest
)
from app.services.analytics.revenue_service import RevenueAnalyticsService


@pytest.mark.asyncio
async def test_realized_revenue_separated_from_open_pipeline(db_session):
    """
    Financial Integrity Rule: Open opportunities must never be counted as realized revenue.
    Lost deals must never count towards realized revenue or open pipeline.
    """
    suffix = uuid.uuid4().hex[:6]
    company = Company(company_name=f"Rev Test Co {suffix}", canonical_domain=f"rev-test-{suffix}.com")
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    # 1. Closed Won Deals (Realized Revenue: $15,000)
    deal_won_1 = CRMDeal(
        company_id=company.id,
        deal_name="Deal Won 1",
        stage="WON",
        outcome="WON",
        estimated_value=10000.0,
        closed_amount=10000.0,
        currency="USD",
        actual_close_date=datetime.now(timezone.utc)
    )
    deal_won_2 = CRMDeal(
        company_id=company.id,
        deal_name="Deal Won 2",
        stage="WON",
        outcome="WON",
        estimated_value=5000.0,
        closed_amount=5000.0,
        currency="USD",
        actual_close_date=datetime.now(timezone.utc)
    )

    # 2. Open Pipeline Deals (Active Pipeline: $50,000)
    deal_open_1 = CRMDeal(
        company_id=company.id,
        deal_name="Deal Open Discovery",
        stage="DISCOVERY",
        outcome=None,
        estimated_value=20000.0,
        currency="USD"
    )
    deal_open_2 = CRMDeal(
        company_id=company.id,
        deal_name="Deal Open Proposal",
        stage="PROPOSAL",
        outcome=None,
        estimated_value=30000.0,
        currency="USD"
    )

    # 3. Lost Deal ($25,000) - Must be excluded from both
    deal_lost = CRMDeal(
        company_id=company.id,
        deal_name="Deal Lost",
        stage="LOST",
        outcome="LOST",
        estimated_value=25000.0,
        currency="USD",
        actual_close_date=datetime.now(timezone.utc)
    )

    db_session.add_all([deal_won_1, deal_won_2, deal_open_1, deal_open_2, deal_lost])
    await db_session.commit()

    service = RevenueAnalyticsService(db_session)
    filters = RevenueFilterParams(company_id=company.id)
    summary = await service.get_revenue_summary(filters)

    assert summary.total_realized_revenue == 15000.0, "Realized revenue must strictly equal sum of WON deals"
    assert summary.total_open_pipeline_value == 50000.0, "Open pipeline value must strictly equal active non-closed deals"
    # Weighted pipeline: 20000 * 0.10 (DISCOVERY) + 30000 * 0.50 (PROPOSAL) = 2000 + 15000 = 17000.0
    assert summary.weighted_pipeline_value == 17000.0
    assert summary.deal_count_won == 2
    assert summary.deal_count_lost == 1
    assert summary.deal_count_open == 2
    assert summary.deal_count_total == 5
    assert summary.win_rate_pct == 66.67  # 2 won / (2 won + 1 lost) = 66.67%
    assert summary.average_deal_size_won == 7500.0


@pytest.mark.asyncio
async def test_discounts_taxes_and_refunds_handling(db_session):
    """
    Financial Correctness Rule: Handle discounts, taxes, and refunds explicitly.
    Net Revenue = closed_amount - discounts + taxes - refunds.
    """
    suffix = uuid.uuid4().hex[:6]
    company = Company(company_name=f"Net Rev Corp {suffix}", canonical_domain=f"net-rev-{suffix}.com")
    db_session.add(company)
    await db_session.commit()

    deal = CRMDeal(
        company_id=company.id,
        deal_name="Enterprise Contract",
        stage="WON",
        outcome="WON",
        closed_amount=20000.0,
        discount_amount=2000.0,
        tax_amount=1000.0,
        refunded_amount=500.0,
        currency="USD",
        actual_close_date=datetime.now(timezone.utc)
    )
    db_session.add(deal)
    await db_session.commit()

    service = RevenueAnalyticsService(db_session)
    filters = RevenueFilterParams(company_id=company.id)
    summary = await service.get_revenue_summary(filters)

    assert summary.total_realized_revenue == 20000.0
    assert summary.total_discounts == 2000.0
    assert summary.total_taxes == 1000.0
    assert summary.total_refunds == 500.0
    assert summary.net_realized_revenue == 18500.0  # 20000 - 2000 + 1000 - 500 = 18500


@pytest.mark.asyncio
async def test_cost_and_margin_handling_no_fabrication(db_session):
    """
    Data Integrity Rule: Never fabricate costs or margins.
    Represent unavailable costs as None, not 0.
    """
    suffix = uuid.uuid4().hex[:6]
    company = Company(company_name=f"Cost Test Corp {suffix}", canonical_domain=f"cost-test-{suffix}.com")
    db_session.add(company)
    await db_session.commit()

    # Deal A: No cost recorded
    deal_no_cost = CRMDeal(
        company_id=company.id,
        deal_name="No Cost Recorded Deal",
        stage="WON",
        outcome="WON",
        closed_amount=10000.0,
        cost_amount=None,
        currency="USD",
        actual_close_date=datetime.now(timezone.utc)
    )
    db_session.add(deal_no_cost)
    await db_session.commit()

    service = RevenueAnalyticsService(db_session)
    filters = RevenueFilterParams(company_id=company.id)
    summary = await service.get_revenue_summary(filters)

    assert summary.total_recorded_costs is None, "Missing costs must be represented as None, not 0"
    assert summary.gross_profit is None
    assert summary.gross_margin_pct is None
    assert any("Fulfillment cost data is not recorded" in lim for lim in summary.data_limitations)

    # Deal B: Cost recorded ($4,000 cost on $10,000 deal -> 60% margin)
    deal_with_cost = CRMDeal(
        company_id=company.id,
        deal_name="Verified Cost Deal",
        stage="WON",
        outcome="WON",
        closed_amount=10000.0,
        cost_amount=4000.0,
        currency="USD",
        actual_close_date=datetime.now(timezone.utc)
    )
    db_session.add(deal_with_cost)
    await db_session.commit()

    summary_partial = await service.get_revenue_summary(filters)
    assert summary_partial.total_recorded_costs == 4000.0
    assert summary_partial.cost_coverage_pct == 50.0  # 1 out of 2 won deals has cost
    assert summary_partial.gross_profit == 6000.0
    assert summary_partial.gross_margin_pct == 60.0  # 6000 / 10000 * 100 = 60.0%
    assert any("Partial cost coverage" in lim for lim in summary_partial.data_limitations)


@pytest.mark.asyncio
async def test_currency_normalization_and_native_breakdown(db_session):
    """
    Multi-Currency Rule: Handle currencies explicitly.
    Do not add amounts in different currencies without documented conversion rate.
    Un-normalized native totals must be reported alongside normalized USD.
    """
    suffix = uuid.uuid4().hex[:6]
    company = Company(company_name=f"Currency Corp {suffix}", canonical_domain=f"currency-{suffix}.com")
    db_session.add(company)
    await db_session.commit()

    # Deal in EUR: 10,000 EUR
    deal_eur = CRMDeal(
        company_id=company.id,
        deal_name="European Deal",
        stage="WON",
        outcome="WON",
        closed_amount=10000.0,
        currency="EUR",
        actual_close_date=datetime.now(timezone.utc)
    )
    # Deal in GBP: 5,000 GBP
    deal_gbp = CRMDeal(
        company_id=company.id,
        deal_name="British Deal",
        stage="WON",
        outcome="WON",
        closed_amount=5000.0,
        currency="GBP",
        actual_close_date=datetime.now(timezone.utc)
    )
    # Deal in USD: 10,000 USD
    deal_usd = CRMDeal(
        company_id=company.id,
        deal_name="US Deal",
        stage="WON",
        outcome="WON",
        closed_amount=10000.0,
        currency="USD",
        actual_close_date=datetime.now(timezone.utc)
    )

    db_session.add_all([deal_eur, deal_gbp, deal_usd])
    await db_session.commit()

    service = RevenueAnalyticsService(db_session)
    filters = RevenueFilterParams(company_id=company.id)
    summary = await service.get_revenue_summary(filters)

    # Verify native breakdowns
    assert summary.currency_breakdown_realized["EUR"] == 10000.0
    assert summary.currency_breakdown_realized["GBP"] == 5000.0
    assert summary.currency_breakdown_realized["USD"] == 10000.0

    # Normalized calculation:
    # 10,000 * 1.08 (EUR) = 10,800 USD
    # 5,000 * 1.28 (GBP) = 6,400 USD
    # 10,000 * 1.00 (USD) = 10,000 USD
    # Total = 27,200 USD
    expected_total = round(10000.0 * BENCHMARK_EXCHANGE_RATES_USD["EUR"] + 5000.0 * BENCHMARK_EXCHANGE_RATES_USD["GBP"] + 10000.0, 2)
    assert summary.total_realized_revenue == expected_total
    assert summary.reporting_currency == "USD"
    assert "EUR" in summary.exchange_rates_used


@pytest.mark.asyncio
async def test_sales_cycle_duration_and_invoicing(db_session):
    """
    Tests sales-cycle duration calculation (created_at to actual_close_date)
    and invoicing outstanding balance tracking.
    """
    suffix = uuid.uuid4().hex[:6]
    company = Company(company_name=f"Cycle Corp {suffix}", canonical_domain=f"cycle-{suffix}.com")
    db_session.add(company)
    await db_session.commit()

    t_created = datetime.now(timezone.utc) - timedelta(days=20)
    t_closed = datetime.now(timezone.utc)

    deal = CRMDeal(
        company_id=company.id,
        deal_name="Cycle & Invoiced Deal",
        stage="WON",
        outcome="WON",
        closed_amount=12000.0,
        currency="USD",
        created_at=t_created,
        actual_close_date=t_closed,
        invoice_status="PARTIALLY_PAID",
        invoiced_amount=12000.0,
        paid_amount=8000.0
    )
    db_session.add(deal)
    await db_session.commit()

    service = RevenueAnalyticsService(db_session)
    filters = RevenueFilterParams(company_id=company.id)
    summary = await service.get_revenue_summary(filters)

    assert summary.average_sales_cycle_days is not None
    assert 19.5 <= summary.average_sales_cycle_days <= 20.5
    assert summary.total_invoiced_amount == 12000.0
    assert summary.total_paid_amount == 8000.0
    assert summary.total_outstanding_amount == 4000.0


@pytest.mark.asyncio
async def test_campaign_roi_and_attribution_caveats(db_session):
    """
    Attribution & ROI Rule:
    - Never present correlation as proof that a campaign caused a sale.
    - Clearly disclose insufficient sample sizes (N < 5).
    - Represent unavailable costs as unknown, not zero ROI.
    """
    suffix = uuid.uuid4().hex[:6]
    company = Company(company_name=f"Campaign Test Co {suffix}", canonical_domain=f"camp-test-{suffix}.com")
    campaign = OutreachCampaign(
        name=f"Q4 SEO Outbound {suffix}",
        description="Q4 Technical SEO Outbound Campaign",
        status="ACTIVE"
    )
    db_session.add_all([company, campaign])
    await db_session.commit()
    await db_session.refresh(campaign)

    # 2 won deals attributed to this campaign: Revenue $25,000, Costs $10,000 -> Profit $15,000 (ROI: 150%)
    deal_1 = CRMDeal(
        company_id=company.id,
        campaign_id=campaign.id,
        deal_name="Campaign Deal 1",
        stage="WON",
        outcome="WON",
        closed_amount=15000.0,
        cost_amount=6000.0,
        currency="USD",
        actual_close_date=datetime.now(timezone.utc)
    )
    deal_2 = CRMDeal(
        company_id=company.id,
        campaign_id=campaign.id,
        deal_name="Campaign Deal 2",
        stage="WON",
        outcome="WON",
        closed_amount=10000.0,
        cost_amount=4000.0,
        currency="USD",
        actual_close_date=datetime.now(timezone.utc)
    )
    db_session.add_all([deal_1, deal_2])
    await db_session.commit()

    service = RevenueAnalyticsService(db_session)
    filters = RevenueFilterParams(campaign_id=campaign.id)
    campaign_rois = await service.get_campaign_roi(filters)

    assert len(campaign_rois) >= 1
    target_camp = next(c for c in campaign_rois if c.campaign_id == campaign.id)
    assert target_camp.deals_won == 2
    assert target_camp.realized_revenue == 25000.0
    assert target_camp.recorded_costs == 10000.0
    assert target_camp.net_profit == 15000.0
    assert target_camp.roi_pct == 150.0
    assert target_camp.sample_size == 2
    assert target_camp.has_sufficient_sample is False
    assert any("correlation-based" in c for c in target_camp.caveats)
    assert any("Insufficient sample size" in c for c in target_camp.caveats)


@pytest.mark.asyncio
async def test_funnel_bottleneck_detection(db_session):
    """
    Sales Funnel Rule: Detect sales-stage conversion rates and pipeline bottlenecks.
    """
    suffix = uuid.uuid4().hex[:6]
    company = Company(company_name=f"Funnel Co {suffix}", canonical_domain=f"funnel-{suffix}.com")
    db_session.add(company)
    await db_session.commit()

    # Pipeline distribution:
    # 10 DISCOVERY, 2 QUALIFICATION, 1 PROPOSAL, 1 NEGOTIATION, 1 WON
    deals = []
    for i in range(10):
        deals.append(CRMDeal(company_id=company.id, deal_name=f"Disc {i}", stage="DISCOVERY", estimated_value=5000.0))
    for i in range(2):
        deals.append(CRMDeal(company_id=company.id, deal_name=f"Qual {i}", stage="QUALIFICATION", estimated_value=5000.0))
    deals.append(CRMDeal(company_id=company.id, deal_name="Prop 1", stage="PROPOSAL", estimated_value=5000.0))
    deals.append(CRMDeal(company_id=company.id, deal_name="Neg 1", stage="NEGOTIATION", estimated_value=5000.0))
    deals.append(CRMDeal(company_id=company.id, deal_name="Won 1", stage="WON", outcome="WON", closed_amount=5000.0, actual_close_date=datetime.now(timezone.utc)))

    db_session.add_all(deals)
    await db_session.commit()

    service = RevenueAnalyticsService(db_session)
    filters = RevenueFilterParams(company_id=company.id)
    funnel = await service.get_funnel_analysis(filters)

    assert funnel.total_deals_analyzed == 15
    assert len(funnel.stages) == 6  # 5 stages + LOST
    discovery_stage = next(s for s in funnel.stages if s.stage == "DISCOVERY")
    assert discovery_stage.deal_count == 10
    # Because 10 deals are in DISCOVERY and only 5 deals progressed to QUALIFICATION or beyond:
    # 5 / 15 = 33.3% conversion
    assert discovery_stage.conversion_rate_to_next is not None
    assert funnel.bottleneck_stage is not None
    assert funnel.bottleneck_reason is not None


@pytest.mark.asyncio
async def test_persistent_snapshots_and_api_integration(db_session):
    """
    Tests persistent analytics snapshots creation, listing, and REST API endpoints.
    """
    suffix = uuid.uuid4().hex[:6]
    company = Company(company_name=f"API Snapshot Co {suffix}", canonical_domain=f"api-snap-{suffix}.com")
    db_session.add(company)
    await db_session.commit()

    deal = CRMDeal(
        company_id=company.id,
        deal_name="API Won Deal",
        stage="WON",
        outcome="WON",
        closed_amount=8500.0,
        currency="USD",
        actual_close_date=datetime.now(timezone.utc)
    )
    db_session.add(deal)
    await db_session.commit()

    service = RevenueAnalyticsService(db_session)
    snapshot = await service.create_snapshot(SnapshotCreateRequest(
        period_type="30D",
        created_by="test_auditor"
    ))

    assert snapshot.id is not None
    assert snapshot.total_realized_revenue >= 8500.0
    assert snapshot.created_by == "test_auditor"

    # Verify snapshot persisted in database
    retrieved = await db_session.get(RevenueAnalyticsSnapshot, snapshot.id)
    assert retrieved is not None
    assert retrieved.period_type == "30D"

    # Test HTTP Endpoints via AsyncClient
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Summary
        res_sum = await ac.get("/analytics/revenue")
        assert res_sum.status_code == 200
        data_sum = res_sum.json()
        assert "total_realized_revenue" in data_sum
        assert "total_open_pipeline_value" in data_sum

        # 2. Services
        res_srv = await ac.get("/analytics/services")
        assert res_srv.status_code == 200
        assert isinstance(res_srv.json(), list)

        # 3. Funnel
        res_fnl = await ac.get("/analytics/funnel")
        assert res_fnl.status_code == 200
        data_fnl = res_fnl.json()
        assert "stages" in data_fnl

        # 4. Drilldown deals
        res_dd = await ac.get("/analytics/drilldown/deals")
        assert res_dd.status_code == 200
        data_dd = res_dd.json()
        assert "drilldown_records" in data_dd
        assert data_dd["total_records"] >= 1

        # 5. Snapshots list
        res_snaps = await ac.get("/analytics/snapshots")
        assert res_snaps.status_code == 200
        snaps = res_snaps.json()
        assert len(snaps) >= 1
        assert any(s["id"] == str(snapshot.id) for s in snaps)
