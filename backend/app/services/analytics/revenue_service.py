import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc

from app.models import (
    Company,
    CRMDeal,
    OutreachCampaign,
    MediaPlan,
    MediaPlanItem,
    RevenueAnalyticsSnapshot
)
from app.schemas.analytics import (
    BENCHMARK_EXCHANGE_RATES_USD,
    STAGE_PROBABILITY_WEIGHTS,
    RevenueFilterParams,
    RevenueSummary,
    ServiceRevenueBreakdown,
    ClientRevenueBreakdown,
    CampaignROIBreakdown,
    SalesFunnelStage,
    FunnelAnalysis,
    RevenueTrendItem,
    RevenueDrilldownItem,
    SnapshotCreateRequest,
    SnapshotResponse
)

logger = logging.getLogger(__name__)


class RevenueAnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def normalize_amount(amount: Optional[float], currency: Optional[str]) -> Tuple[float, Optional[str]]:
        """
        Converts an amount to USD using the documented benchmark rate table.
        Returns (normalized_usd_amount, warning_or_limitation_if_unknown).
        """
        if amount is None:
            return 0.0, None
        curr = (currency or "USD").upper().strip()
        if curr in BENCHMARK_EXCHANGE_RATES_USD:
            rate = BENCHMARK_EXCHANGE_RATES_USD[curr]
            return round(amount * rate, 2), None
        else:
            warning = f"Currency '{curr}' is not in benchmark rate table. Parity rate 1.0 used."
            return round(amount, 2), warning

    def _apply_deal_filters(self, query, filters: Optional[RevenueFilterParams] = None):
        """Applies date, service, campaign, company, and currency filters to a CRMDeal query."""
        if not filters:
            return query
        
        conditions = []
        if filters.start_date:
            conditions.append(or_(
                CRMDeal.actual_close_date >= filters.start_date,
                and_(CRMDeal.actual_close_date.is_(None), CRMDeal.created_at >= filters.start_date)
            ))
        if filters.end_date:
            conditions.append(or_(
                CRMDeal.actual_close_date <= filters.end_date,
                and_(CRMDeal.actual_close_date.is_(None), CRMDeal.created_at <= filters.end_date)
            ))
        if filters.service_category:
            conditions.append(CRMDeal.service_category == filters.service_category.upper().strip())
        if filters.campaign_id:
            conditions.append(CRMDeal.campaign_id == filters.campaign_id)
        if filters.company_id:
            conditions.append(CRMDeal.company_id == filters.company_id)
        if filters.currency:
            conditions.append(func.upper(CRMDeal.currency) == filters.currency.upper().strip())

        if conditions:
            query = query.where(and_(*conditions))
        return query

    async def get_revenue_summary(self, filters: Optional[RevenueFilterParams] = None) -> RevenueSummary:
        """
        Calculates high-integrity revenue summary:
        - Realized revenue (WON only) with net adjustments (discounts, taxes, refunds)
        - Open pipeline value (strictly separated from realized revenue)
        - Weighted pipeline value
        - Cost and margin analysis with missing-cost disclosure
        - Multi-currency breakdowns
        - Sales cycle duration and win rates
        """
        query = select(CRMDeal)
        query = self._apply_deal_filters(query, filters)
        result = await self.session.execute(query)
        deals: List[CRMDeal] = list(result.scalars().all())

        total_realized_revenue = 0.0
        total_discounts = 0.0
        total_taxes = 0.0
        total_refunds = 0.0

        total_open_pipeline_value = 0.0
        weighted_pipeline_value = 0.0

        deal_count_won = 0
        deal_count_lost = 0
        deal_count_open = 0

        total_invoiced = 0.0
        total_paid = 0.0
        has_invoice_data = False

        currency_won: Dict[str, float] = {}
        currency_open: Dict[str, float] = {}
        data_limitations: List[str] = []
        unknown_currencies: set = set()

        won_deals_cycle_days: List[float] = []

        # Cost tracking for won deals
        total_recorded_costs = 0.0
        won_revenue_with_costs = 0.0
        won_deals_with_cost_count = 0

        # Pre-fetch media plan costs if needed
        media_plan_costs: Dict[uuid.UUID, float] = {}
        media_plan_ids = [d.media_plan_id for d in deals if d.media_plan_id and d.cost_amount is None]
        if media_plan_ids:
            mp_query = select(
                MediaPlanItem.media_plan_id,
                func.sum(MediaPlanItem.proposed_price)
            ).where(MediaPlanItem.media_plan_id.in_(media_plan_ids)).group_by(MediaPlanItem.media_plan_id)
            mp_res = await self.session.execute(mp_query)
            for mp_id, total_mp_cost in mp_res.all():
                if total_mp_cost is not None:
                    media_plan_costs[mp_id] = float(total_mp_cost)

        for deal in deals:
            curr = (deal.currency or "USD").upper().strip()
            
            # Check for unknown currencies
            if curr not in BENCHMARK_EXCHANGE_RATES_USD:
                unknown_currencies.add(curr)

            is_won = (deal.stage == "WON" or deal.outcome == "WON")
            is_lost = (deal.stage == "LOST" or deal.outcome == "LOST")

            if is_won:
                deal_count_won += 1
                native_won_amt = deal.closed_amount if deal.closed_amount is not None else (deal.proposed_value or deal.estimated_value or 0.0)
                norm_won_amt, _ = self.normalize_amount(native_won_amt, curr)
                total_realized_revenue += norm_won_amt

                # Currency breakdown
                currency_won[curr] = round(currency_won.get(curr, 0.0) + native_won_amt, 2)

                # Discounts, taxes, refunds
                norm_discount, _ = self.normalize_amount(deal.discount_amount or 0.0, curr)
                norm_tax, _ = self.normalize_amount(deal.tax_amount or 0.0, curr)
                norm_refund, _ = self.normalize_amount(deal.refunded_amount or 0.0, curr)
                total_discounts += norm_discount
                total_taxes += norm_tax
                total_refunds += norm_refund

                # Invoicing & payments
                if deal.invoiced_amount is not None:
                    has_invoice_data = True
                    norm_inv, _ = self.normalize_amount(deal.invoiced_amount, curr)
                    total_invoiced += norm_inv
                if deal.paid_amount is not None:
                    has_invoice_data = True
                    norm_paid, _ = self.normalize_amount(deal.paid_amount, curr)
                    total_paid += norm_paid

                # Sales cycle duration
                if deal.created_at and deal.actual_close_date:
                    delta = deal.actual_close_date - deal.created_at
                    days = max(0.0, delta.total_seconds() / 86400.0)
                    won_deals_cycle_days.append(days)

                # Cost evaluation
                deal_cost = deal.cost_amount
                if deal_cost is None and deal.media_plan_id and deal.media_plan_id in media_plan_costs:
                    deal_cost = media_plan_costs[deal.media_plan_id]
                
                if deal_cost is not None:
                    norm_cost, _ = self.normalize_amount(deal_cost, curr)
                    total_recorded_costs += norm_cost
                    won_revenue_with_costs += norm_won_amt
                    won_deals_with_cost_count += 1

            elif is_lost:
                deal_count_lost += 1
            else:
                # Active open pipeline
                deal_count_open += 1
                native_est = deal.estimated_value or 0.0
                norm_est, _ = self.normalize_amount(native_est, curr)
                total_open_pipeline_value += norm_est

                prob_weight = STAGE_PROBABILITY_WEIGHTS.get(deal.stage, 0.20)
                weighted_pipeline_value += norm_est * prob_weight

                currency_open[curr] = round(currency_open.get(curr, 0.0) + native_est, 2)

        # Net Realized Revenue
        net_realized_revenue = round(total_realized_revenue - total_discounts + total_taxes - total_refunds, 2)
        total_realized_revenue = round(total_realized_revenue, 2)
        total_open_pipeline_value = round(total_open_pipeline_value, 2)
        weighted_pipeline_value = round(weighted_pipeline_value, 2)

        # Win rate
        closed_decisions = deal_count_won + deal_count_lost
        win_rate_pct = round((deal_count_won / closed_decisions) * 100, 2) if closed_decisions > 0 else 0.0

        # Average deal size
        avg_deal_size = round(total_realized_revenue / deal_count_won, 2) if deal_count_won > 0 else None

        # Average sales cycle days
        avg_cycle_days = round(sum(won_deals_cycle_days) / len(won_deals_cycle_days), 1) if won_deals_cycle_days else None

        # Profitability & Margins (never fabricate costs)
        cost_coverage_pct = round((won_deals_with_cost_count / deal_count_won) * 100, 1) if deal_count_won > 0 else 0.0
        gross_profit = None
        gross_margin_pct = None
        final_recorded_costs = None

        if deal_count_won > 0:
            if won_deals_with_cost_count == 0:
                final_recorded_costs = None
                data_limitations.append("Fulfillment cost data is not recorded for closed-won deals. Margins cannot be calculated without fabrication.")
            else:
                final_recorded_costs = round(total_recorded_costs, 2)
                gross_profit = round(won_revenue_with_costs - final_recorded_costs, 2)
                if won_revenue_with_costs > 0:
                    gross_margin_pct = round((gross_profit / won_revenue_with_costs) * 100, 2)
                if won_deals_with_cost_count < deal_count_won:
                    data_limitations.append(
                        f"Partial cost coverage: {cost_coverage_pct}% of closed-won deals have recorded costs. "
                        f"Reported gross margin ({gross_margin_pct}%) is computed strictly over deals with verified costs."
                    )
        else:
            final_recorded_costs = None

        # Invoicing
        final_invoiced = round(total_invoiced, 2) if has_invoice_data else None
        final_paid = round(total_paid, 2) if has_invoice_data else None
        final_outstanding = round(total_invoiced - total_paid, 2) if has_invoice_data else None
        if not has_invoice_data:
            data_limitations.append("No invoice records exist in the current deal set. Invoicing and cashflow totals represented as unavailable.")

        if unknown_currencies:
            data_limitations.append(f"Encountered currencies {list(unknown_currencies)} not present in benchmark table; 1:1 parity applied.")

        return RevenueSummary(
            reporting_currency="USD",
            total_realized_revenue=total_realized_revenue,
            net_realized_revenue=net_realized_revenue,
            total_discounts=round(total_discounts, 2),
            total_taxes=round(total_taxes, 2),
            total_refunds=round(total_refunds, 2),
            total_open_pipeline_value=total_open_pipeline_value,
            weighted_pipeline_value=weighted_pipeline_value,
            total_recorded_costs=final_recorded_costs,
            cost_coverage_pct=cost_coverage_pct,
            gross_profit=gross_profit,
            gross_margin_pct=gross_margin_pct,
            total_invoiced_amount=final_invoiced,
            total_paid_amount=final_paid,
            total_outstanding_amount=final_outstanding,
            deal_count_total=len(deals),
            deal_count_won=deal_count_won,
            deal_count_lost=deal_count_lost,
            deal_count_open=deal_count_open,
            win_rate_pct=win_rate_pct,
            average_deal_size_won=avg_deal_size,
            average_sales_cycle_days=avg_cycle_days,
            currency_breakdown_realized=currency_won,
            currency_breakdown_pipeline=currency_open,
            data_limitations=data_limitations
        )

    async def get_revenue_by_service(self, filters: Optional[RevenueFilterParams] = None) -> List[ServiceRevenueBreakdown]:
        """Calculates revenue and pipeline metrics segmented by service category."""
        query = select(CRMDeal)
        query = self._apply_deal_filters(query, filters)
        result = await self.session.execute(query)
        deals = list(result.scalars().all())

        # Group deals by service_category
        categories: Dict[str, List[CRMDeal]] = {}
        for deal in deals:
            cat = deal.service_category or "OTHER"
            categories.setdefault(cat, []).append(deal)

        breakdowns: List[ServiceRevenueBreakdown] = []
        for cat, cat_deals in sorted(categories.items()):
            realized = 0.0
            pipeline = 0.0
            won_count = 0
            open_count = 0
            cat_costs = 0.0
            cat_cost_won_rev = 0.0
            has_costs = False

            for deal in cat_deals:
                curr = (deal.currency or "USD").upper().strip()
                is_won = (deal.stage == "WON" or deal.outcome == "WON")
                is_lost = (deal.stage == "LOST" or deal.outcome == "LOST")

                if is_won:
                    won_count += 1
                    amt = deal.closed_amount if deal.closed_amount is not None else (deal.proposed_value or deal.estimated_value or 0.0)
                    norm_amt, _ = self.normalize_amount(amt, curr)
                    realized += norm_amt

                    if deal.cost_amount is not None:
                        has_costs = True
                        norm_cost, _ = self.normalize_amount(deal.cost_amount, curr)
                        cat_costs += norm_cost
                        cat_cost_won_rev += norm_amt
                elif not is_lost:
                    open_count += 1
                    norm_est, _ = self.normalize_amount(deal.estimated_value, curr)
                    pipeline += norm_est

            avg_deal_size = round(realized / won_count, 2) if won_count > 0 else None
            gross_profit = None
            gross_margin = None
            final_costs = None
            if has_costs and cat_cost_won_rev > 0:
                final_costs = round(cat_costs, 2)
                gross_profit = round(cat_cost_won_rev - cat_costs, 2)
                gross_margin = round((gross_profit / cat_cost_won_rev) * 100, 2)

            breakdowns.append(ServiceRevenueBreakdown(
                service_category=cat,
                realized_revenue=round(realized, 2),
                deals_won=won_count,
                average_deal_size=avg_deal_size,
                open_pipeline_value=round(pipeline, 2),
                open_deal_count=open_count,
                recorded_costs=final_costs,
                gross_profit=gross_profit,
                gross_margin_pct=gross_margin
            ))

        return breakdowns

    async def get_revenue_by_client(self, filters: Optional[RevenueFilterParams] = None, limit: int = 25) -> List[ClientRevenueBreakdown]:
        """Calculates revenue and active pipeline segmented by client/prospect company."""
        query = select(CRMDeal, Company).join(Company, CRMDeal.company_id == Company.id)
        query = self._apply_deal_filters(query, filters)
        result = await self.session.execute(query)
        rows = result.all()

        companies: Dict[uuid.UUID, Dict[str, Any]] = {}
        for deal, company in rows:
            cid = company.id
            if cid not in companies:
                companies[cid] = {
                    "company_id": cid,
                    "company_name": company.company_name or "Unknown",
                    "domain": company.canonical_domain,
                    "sales_stage": company.sales_stage,
                    "realized_revenue": 0.0,
                    "deals_won": 0,
                    "open_pipeline_value": 0.0,
                    "open_deal_count": 0,
                    "last_deal_date": None
                }

            curr = (deal.currency or "USD").upper().strip()
            is_won = (deal.stage == "WON" or deal.outcome == "WON")
            is_lost = (deal.stage == "LOST" or deal.outcome == "LOST")

            deal_date = deal.actual_close_date or deal.created_at
            if deal_date:
                curr_last = companies[cid]["last_deal_date"]
                if not curr_last or deal_date > curr_last:
                    companies[cid]["last_deal_date"] = deal_date

            if is_won:
                companies[cid]["deals_won"] += 1
                amt = deal.closed_amount if deal.closed_amount is not None else (deal.proposed_value or deal.estimated_value or 0.0)
                norm_amt, _ = self.normalize_amount(amt, curr)
                companies[cid]["realized_revenue"] += norm_amt
            elif not is_lost:
                companies[cid]["open_deal_count"] += 1
                norm_est, _ = self.normalize_amount(deal.estimated_value, curr)
                companies[cid]["open_pipeline_value"] += norm_est

        result_list = [
            ClientRevenueBreakdown(
                company_id=c["company_id"],
                company_name=c["company_name"],
                domain=c["domain"],
                sales_stage=c["sales_stage"],
                realized_revenue=round(c["realized_revenue"], 2),
                deals_won=c["deals_won"],
                open_pipeline_value=round(c["open_pipeline_value"], 2),
                open_deal_count=c["open_deal_count"],
                last_deal_date=c["last_deal_date"]
            )
            for c in companies.values()
        ]

        # Sort by realized revenue descending, then open pipeline
        result_list.sort(key=lambda x: (x.realized_revenue, x.open_pipeline_value), reverse=True)
        return result_list[:limit]

    async def get_campaign_roi(self, filters: Optional[RevenueFilterParams] = None) -> List[CampaignROIBreakdown]:
        """
        Calculates campaign-attributed realized revenue, recorded costs, and ROI.
        Strict disclosure rules:
        - If sample size < 5, flags as insufficient sample.
        - Attributed causality is explicitly marked as correlation-based.
        - If cost data is missing/unknown, ROI is represented as None, not 0.
        """
        query = select(CRMDeal, OutreachCampaign).outerjoin(OutreachCampaign, CRMDeal.campaign_id == OutreachCampaign.id)
        query = self._apply_deal_filters(query, filters)
        result = await self.session.execute(query)
        rows = result.all()

        campaign_map: Dict[Optional[uuid.UUID], Dict[str, Any]] = {}

        for deal, campaign in rows:
            camp_id = campaign.id if campaign else None
            camp_name = campaign.name if campaign else "Direct / Unattributed CRM Pipeline"

            if camp_id not in campaign_map:
                campaign_map[camp_id] = {
                    "campaign_id": camp_id,
                    "campaign_name": camp_name,
                    "deals_won": 0,
                    "deal_count_total": 0,
                    "realized_revenue": 0.0,
                    "recorded_costs": 0.0,
                    "has_costs": False,
                    "caveats": []
                }

            campaign_map[camp_id]["deal_count_total"] += 1
            curr = (deal.currency or "USD").upper().strip()
            is_won = (deal.stage == "WON" or deal.outcome == "WON")

            if is_won:
                campaign_map[camp_id]["deals_won"] += 1
                amt = deal.closed_amount if deal.closed_amount is not None else (deal.proposed_value or deal.estimated_value or 0.0)
                norm_amt, _ = self.normalize_amount(amt, curr)
                campaign_map[camp_id]["realized_revenue"] += norm_amt

                if deal.cost_amount is not None:
                    campaign_map[camp_id]["has_costs"] = True
                    norm_cost, _ = self.normalize_amount(deal.cost_amount, curr)
                    campaign_map[camp_id]["recorded_costs"] += norm_cost

        breakdowns: List[CampaignROIBreakdown] = []
        for camp_id, data in campaign_map.items():
            sample_size = data["deal_count_total"]
            has_sufficient = sample_size >= 5
            caveats = [
                "Campaign attribution is correlation-based; sales-cycle causality is not guaranteed."
            ]
            if not has_sufficient:
                caveats.append(f"Insufficient sample size ({sample_size} deals). Minimum 5 deals recommended for statistical stability.")

            recorded_costs = round(data["recorded_costs"], 2) if data["has_costs"] else None
            net_profit = None
            roi_pct = None

            if recorded_costs is not None:
                net_profit = round(data["realized_revenue"] - recorded_costs, 2)
                if recorded_costs > 0:
                    roi_pct = round(((data["realized_revenue"] - recorded_costs) / recorded_costs) * 100, 2)
                else:
                    caveats.append("Recorded cost is zero; percentage ROI cannot be computed.")
            else:
                caveats.append("Campaign fulfillment cost data unavailable. ROI cannot be computed without cost records.")

            breakdowns.append(CampaignROIBreakdown(
                campaign_id=camp_id,
                campaign_name=data["campaign_name"],
                deals_won=data["deals_won"],
                deal_count_total=data["deal_count_total"],
                realized_revenue=round(data["realized_revenue"], 2),
                recorded_costs=recorded_costs,
                net_profit=net_profit,
                roi_pct=roi_pct,
                sample_size=sample_size,
                has_sufficient_sample=has_sufficient,
                caveats=caveats
            ))

        breakdowns.sort(key=lambda x: x.realized_revenue, reverse=True)
        return breakdowns

    async def get_funnel_analysis(self, filters: Optional[RevenueFilterParams] = None) -> FunnelAnalysis:
        """
        Analyzes sales stage progression:
        DISCOVERY -> QUALIFICATION -> PROPOSAL -> NEGOTIATION -> WON
        Identifies stage-to-stage transition conversion rates and bottleneck stage.
        """
        query = select(CRMDeal)
        query = self._apply_deal_filters(query, filters)
        result = await self.session.execute(query)
        deals = list(result.scalars().all())

        stage_order = [
            ("DISCOVERY", 1, 0.10),
            ("QUALIFICATION", 2, 0.25),
            ("PROPOSAL", 3, 0.50),
            ("NEGOTIATION", 4, 0.75),
            ("WON", 5, 1.00),
            ("LOST", 6, 0.00)
        ]

        stage_counts: Dict[str, int] = {st: 0 for st, _, _ in stage_order}
        stage_values: Dict[str, float] = {st: 0.0 for st, _, _ in stage_order}

        for deal in deals:
            curr = (deal.currency or "USD").upper().strip()
            st = (deal.stage or "DISCOVERY").upper().strip()
            if deal.outcome == "WON" and st != "WON":
                st = "WON"
            elif deal.outcome == "LOST" and st != "LOST":
                st = "LOST"

            if st not in stage_counts:
                st = "DISCOVERY"

            stage_counts[st] += 1
            if st == "WON":
                amt = deal.closed_amount if deal.closed_amount is not None else (deal.proposed_value or deal.estimated_value or 0.0)
            else:
                amt = deal.estimated_value or 0.0
            norm_amt, _ = self.normalize_amount(amt, curr)
            stage_values[st] += norm_amt

        # Compute pipeline progression stages
        pipeline_stages = ["DISCOVERY", "QUALIFICATION", "PROPOSAL", "NEGOTIATION", "WON"]
        stages_res: List[SalesFunnelStage] = []

        total_active_plus_won = sum(stage_counts[st] for st in pipeline_stages) + stage_counts["LOST"]

        bottleneck_stage: Optional[str] = None
        lowest_conversion: float = 100.0
        bottleneck_reason: Optional[str] = None

        for idx, st_name in enumerate(pipeline_stages):
            cnt = stage_counts[st_name]
            val = round(stage_values[st_name], 2)
            order = idx + 1
            weight = STAGE_PROBABILITY_WEIGHTS.get(st_name, 0.2)
            weighted_val = round(val * weight, 2)

            # Conversion rate to next stage
            conv_rate = None
            dropoff_rate = None
            if idx < len(pipeline_stages) - 1:
                next_stage_name = pipeline_stages[idx + 1]
                # In current pipeline distribution, compare volume reaching next stages vs current
                # Cumulative deals that reached or surpassed current stage
                curr_and_beyond = sum(stage_counts[pipeline_stages[j]] for j in range(idx, len(pipeline_stages)))
                next_and_beyond = sum(stage_counts[pipeline_stages[j]] for j in range(idx + 1, len(pipeline_stages)))

                if curr_and_beyond > 0:
                    conv_rate = round((next_and_beyond / curr_and_beyond) * 100, 1)
                    dropoff_rate = round(100.0 - conv_rate, 1)
                    
                    if conv_rate < lowest_conversion and curr_and_beyond >= 2:
                        lowest_conversion = conv_rate
                        bottleneck_stage = st_name
                        bottleneck_reason = (
                            f"Stage '{st_name}' exhibits the lowest progression rate ({conv_rate}%) "
                            f"with a {dropoff_rate}% drop-off into subsequent stages."
                        )

            stages_res.append(SalesFunnelStage(
                stage=st_name,
                order=order,
                deal_count=cnt,
                total_value=val,
                probability_weight=weight,
                weighted_value=weighted_val,
                conversion_rate_to_next=conv_rate,
                dropoff_rate=dropoff_rate,
                avg_days_in_stage=None
            ))

        # Include LOST as terminal stage in stages list
        stages_res.append(SalesFunnelStage(
            stage="LOST",
            order=6,
            deal_count=stage_counts["LOST"],
            total_value=round(stage_values["LOST"], 2),
            probability_weight=0.0,
            weighted_value=0.0,
            conversion_rate_to_next=None,
            dropoff_rate=None,
            avg_days_in_stage=None
        ))

        won_count = stage_counts["WON"]
        overall_conversion = round((won_count / total_active_plus_won) * 100, 2) if total_active_plus_won > 0 else 0.0

        return FunnelAnalysis(
            stages=stages_res,
            overall_conversion_rate=overall_conversion,
            bottleneck_stage=bottleneck_stage,
            bottleneck_reason=bottleneck_reason,
            total_deals_analyzed=total_active_plus_won
        )

    async def get_revenue_trends(self, filters: Optional[RevenueFilterParams] = None, interval: str = "monthly") -> List[RevenueTrendItem]:
        """Calculates historical revenue and pipeline creation trend series."""
        query = select(CRMDeal)
        query = self._apply_deal_filters(query, filters)
        result = await self.session.execute(query)
        deals = list(result.scalars().all())

        trends: Dict[str, Dict[str, Any]] = {}

        for deal in deals:
            curr = (deal.currency or "USD").upper().strip()
            is_won = (deal.stage == "WON" or deal.outcome == "WON")

            # Determine key period for deal creation
            created_dt = deal.created_at or datetime.now(timezone.utc)
            created_period = created_dt.strftime("%Y-%m") if interval == "monthly" else created_dt.strftime("%Y-%m-%d")

            trends.setdefault(created_period, {
                "period": created_period,
                "realized_revenue": 0.0,
                "deals_won": 0,
                "pipeline_created_value": 0.0,
                "deals_created": 0
            })
            trends[created_period]["deals_created"] += 1
            norm_est, _ = self.normalize_amount(deal.estimated_value or 0.0, curr)
            trends[created_period]["pipeline_created_value"] += norm_est

            if is_won:
                close_dt = deal.actual_close_date or deal.created_at or datetime.now(timezone.utc)
                won_period = close_dt.strftime("%Y-%m") if interval == "monthly" else close_dt.strftime("%Y-%m-%d")
                trends.setdefault(won_period, {
                    "period": won_period,
                    "realized_revenue": 0.0,
                    "deals_won": 0,
                    "pipeline_created_value": 0.0,
                    "deals_created": 0
                })
                trends[won_period]["deals_won"] += 1
                amt = deal.closed_amount if deal.closed_amount is not None else (deal.proposed_value or deal.estimated_value or 0.0)
                norm_amt, _ = self.normalize_amount(amt, curr)
                trends[won_period]["realized_revenue"] += norm_amt

        sorted_trends = [
            RevenueTrendItem(
                period=p,
                realized_revenue=round(d["realized_revenue"], 2),
                deals_won=d["deals_won"],
                pipeline_created_value=round(d["pipeline_created_value"], 2),
                deals_created=d["deals_created"]
            )
            for p, d in sorted(trends.items())
        ]
        return sorted_trends

    async def get_deals_drilldown(
        self,
        filters: Optional[RevenueFilterParams] = None,
        stage: Optional[str] = None,
        outcome: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """Provides verified record drilldowns with complete calculation provenance."""
        query = select(CRMDeal, Company, OutreachCampaign).join(Company, CRMDeal.company_id == Company.id).outerjoin(OutreachCampaign, CRMDeal.campaign_id == OutreachCampaign.id)
        query = self._apply_deal_filters(query, filters)

        if stage:
            query = query.where(CRMDeal.stage == stage.upper().strip())
        if outcome:
            query = query.where(CRMDeal.outcome == outcome.upper().strip())

        # Count total
        count_q = select(func.count(CRMDeal.id))
        count_q = self._apply_deal_filters(count_q, filters)
        if stage:
            count_q = count_q.where(CRMDeal.stage == stage.upper().strip())
        if outcome:
            count_q = count_q.where(CRMDeal.outcome == outcome.upper().strip())
        
        count_res = await self.session.execute(count_q)
        total_count = count_res.scalar() or 0

        # Paginated fetch
        query = query.order_by(desc(CRMDeal.created_at)).offset((page - 1) * page_size).limit(page_size)
        res = await self.session.execute(query)
        rows = res.all()

        items: List[RevenueDrilldownItem] = []
        for deal, company, campaign in rows:
            curr = (deal.currency or "USD").upper().strip()
            norm_closed, _ = self.normalize_amount(deal.closed_amount, curr) if deal.closed_amount is not None else (None, None)
            norm_est, _ = self.normalize_amount(deal.estimated_value, curr)

            sales_cycle_days = None
            if deal.created_at and deal.actual_close_date:
                delta = deal.actual_close_date - deal.created_at
                sales_cycle_days = round(max(0.0, delta.total_seconds() / 86400.0), 1)

            margin = None
            if deal.cost_amount is not None and deal.closed_amount and deal.closed_amount > 0:
                profit = deal.closed_amount - deal.cost_amount
                margin = round((profit / deal.closed_amount) * 100, 2)

            items.append(RevenueDrilldownItem(
                id=deal.id,
                deal_name=deal.deal_name,
                company_id=company.id,
                company_name=company.company_name or "Unknown",
                service_category=deal.service_category or "FULL_SERVICE",
                stage=deal.stage or "DISCOVERY",
                outcome=deal.outcome,
                currency=curr,
                native_closed_amount=deal.closed_amount,
                normalized_closed_amount=norm_closed,
                native_estimated_value=deal.estimated_value or 0.0,
                normalized_estimated_value=norm_est,
                cost_amount=deal.cost_amount,
                gross_margin_pct=margin,
                invoice_status=deal.invoice_status,
                invoiced_amount=deal.invoiced_amount,
                paid_amount=deal.paid_amount,
                discount_amount=deal.discount_amount or 0.0,
                tax_amount=deal.tax_amount or 0.0,
                refunded_amount=deal.refunded_amount or 0.0,
                created_at=deal.created_at,
                actual_close_date=deal.actual_close_date,
                sales_cycle_days=sales_cycle_days,
                campaign_id=campaign.id if campaign else None,
                campaign_name=campaign.name if campaign else None
            ))

        return {
            "total_records": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, (total_count + page_size - 1) // page_size),
            "drilldown_records": items,
            "calculation_notes": [
                "Normalized values converted to USD using benchmark policy exchange table.",
                "Sales cycle duration calculated as elapsed days between deal creation and actual close date."
            ]
        }

    async def create_snapshot(self, request: SnapshotCreateRequest) -> RevenueAnalyticsSnapshot:
        """Computes comprehensive analytics and persists an audited snapshot to database."""
        filters = RevenueFilterParams(
            start_date=request.period_start,
            end_date=request.period_end
        )
        summary = await self.get_revenue_summary(filters)
        services = await self.get_revenue_by_service(filters)
        clients = await self.get_revenue_by_client(filters, limit=15)
        campaigns = await self.get_campaign_roi(filters)
        funnel = await self.get_funnel_analysis(filters)

        snapshot = RevenueAnalyticsSnapshot(
            period_start=request.period_start,
            period_end=request.period_end,
            period_type=request.period_type,
            reporting_currency=summary.reporting_currency,
            total_realized_revenue=summary.total_realized_revenue,
            total_open_pipeline_value=summary.total_open_pipeline_value,
            weighted_pipeline_value=summary.weighted_pipeline_value,
            total_recorded_costs=summary.total_recorded_costs,
            gross_profit=summary.gross_profit,
            gross_margin_pct=summary.gross_margin_pct,
            deal_count_won=summary.deal_count_won,
            deal_count_lost=summary.deal_count_lost,
            deal_count_open=summary.deal_count_open,
            average_deal_size_won=summary.average_deal_size_won,
            average_sales_cycle_days=summary.average_sales_cycle_days,
            revenue_by_service={s.service_category: s.model_dump() for s in services},
            revenue_by_client=[c.model_dump(mode="json") for c in clients],
            revenue_by_campaign=[c.model_dump(mode="json") for c in campaigns],
            funnel_metrics=funnel.model_dump(),
            currency_breakdown={
                "realized": summary.currency_breakdown_realized,
                "pipeline": summary.currency_breakdown_pipeline
            },
            data_limitations=summary.data_limitations,
            created_by=request.created_by or "system"
        )
        self.session.add(snapshot)
        await self.session.commit()
        await self.session.refresh(snapshot)
        logger.info(f"Created RevenueAnalyticsSnapshot {snapshot.id} for period {snapshot.period_type}")
        return snapshot

    async def list_snapshots(self, limit: int = 20) -> List[RevenueAnalyticsSnapshot]:
        """Retrieves recent saved revenue analytics snapshots."""
        query = select(RevenueAnalyticsSnapshot).order_by(desc(RevenueAnalyticsSnapshot.created_at)).limit(limit)
        res = await self.session.execute(query)
        return list(res.scalars().all())
