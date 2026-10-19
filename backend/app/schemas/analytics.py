import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# Documented Exchange Rates to USD (Baseline: ECB / Federal Reserve Reference Benchmark)
BENCHMARK_EXCHANGE_RATES_USD: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.28,
    "CAD": 0.74,
    "AUD": 0.66,
}

# Pipeline Stage Probability Weights
STAGE_PROBABILITY_WEIGHTS: Dict[str, float] = {
    "DISCOVERY": 0.10,
    "QUALIFICATION": 0.25,
    "PROPOSAL": 0.50,
    "NEGOTIATION": 0.75,
    "WON": 1.00,
    "LOST": 0.00,
}


class RevenueFilterParams(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    service_category: Optional[str] = None
    campaign_id: Optional[uuid.UUID] = None
    company_id: Optional[uuid.UUID] = None
    currency: Optional[str] = None


class RevenueSummary(BaseModel):
    reporting_currency: str = "USD"
    exchange_rates_used: Dict[str, float] = Field(default_factory=lambda: BENCHMARK_EXCHANGE_RATES_USD)
    rates_as_of: str = "2026-10-11 (Benchmark Policy Table)"
    
    # Realized Revenue (WON only)
    total_realized_revenue: float = 0.0
    net_realized_revenue: float = 0.0
    total_discounts: float = 0.0
    total_taxes: float = 0.0
    total_refunds: float = 0.0
    
    # Pipeline Value (Excludes Realized Revenue)
    total_open_pipeline_value: float = 0.0
    weighted_pipeline_value: float = 0.0
    
    # Costs & Profitability (None if unavailable)
    total_recorded_costs: Optional[float] = None
    cost_coverage_pct: float = 0.0
    gross_profit: Optional[float] = None
    gross_margin_pct: Optional[float] = None
    
    # Invoicing & Cashflow
    total_invoiced_amount: Optional[float] = None
    total_paid_amount: Optional[float] = None
    total_outstanding_amount: Optional[float] = None
    
    # Deal Counts & Performance Metrics
    deal_count_total: int = 0
    deal_count_won: int = 0
    deal_count_lost: int = 0
    deal_count_open: int = 0
    win_rate_pct: float = 0.0
    average_deal_size_won: Optional[float] = None
    average_sales_cycle_days: Optional[float] = None
    
    # Native Currency Breakdowns (Before Normalization)
    currency_breakdown_realized: Dict[str, float] = Field(default_factory=dict)
    currency_breakdown_pipeline: Dict[str, float] = Field(default_factory=dict)
    
    # Limitations & Disclosures
    data_limitations: List[str] = Field(default_factory=list)


class ServiceRevenueBreakdown(BaseModel):
    service_category: str
    realized_revenue: float = 0.0
    deals_won: int = 0
    average_deal_size: Optional[float] = None
    open_pipeline_value: float = 0.0
    open_deal_count: int = 0
    recorded_costs: Optional[float] = None
    gross_profit: Optional[float] = None
    gross_margin_pct: Optional[float] = None


class ClientRevenueBreakdown(BaseModel):
    company_id: uuid.UUID
    company_name: str
    domain: Optional[str] = None
    sales_stage: str
    realized_revenue: float = 0.0
    deals_won: int = 0
    open_pipeline_value: float = 0.0
    open_deal_count: int = 0
    last_deal_date: Optional[datetime] = None


class CampaignROIBreakdown(BaseModel):
    campaign_id: Optional[uuid.UUID] = None
    campaign_name: str
    deals_won: int = 0
    deal_count_total: int = 0
    realized_revenue: float = 0.0
    recorded_costs: Optional[float] = None
    net_profit: Optional[float] = None
    roi_pct: Optional[float] = None
    attribution_model: str = "First/Direct Deal Association (Correlation-Based)"
    sample_size: int = 0
    has_sufficient_sample: bool = False
    caveats: List[str] = Field(default_factory=list)


class SalesFunnelStage(BaseModel):
    stage: str
    order: int
    deal_count: int
    total_value: float
    probability_weight: float
    weighted_value: float
    conversion_rate_to_next: Optional[float] = None
    dropoff_rate: Optional[float] = None
    avg_days_in_stage: Optional[float] = None


class FunnelAnalysis(BaseModel):
    stages: List[SalesFunnelStage]
    overall_conversion_rate: float = 0.0
    bottleneck_stage: Optional[str] = None
    bottleneck_reason: Optional[str] = None
    total_deals_analyzed: int = 0


class RevenueTrendItem(BaseModel):
    period: str # YYYY-MM or YYYY-WW or YYYY-MM-DD
    realized_revenue: float = 0.0
    deals_won: int = 0
    pipeline_created_value: float = 0.0
    deals_created: int = 0


class RevenueDrilldownItem(BaseModel):
    id: uuid.UUID
    deal_name: str
    company_id: uuid.UUID
    company_name: str
    service_category: str
    stage: str
    outcome: Optional[str] = None
    currency: str
    native_closed_amount: Optional[float] = None
    normalized_closed_amount: Optional[float] = None
    native_estimated_value: float
    normalized_estimated_value: float
    cost_amount: Optional[float] = None
    gross_margin_pct: Optional[float] = None
    invoice_status: Optional[str] = None
    invoiced_amount: Optional[float] = None
    paid_amount: Optional[float] = None
    discount_amount: Optional[float] = 0.0
    tax_amount: Optional[float] = 0.0
    refunded_amount: Optional[float] = 0.0
    created_at: datetime
    actual_close_date: Optional[datetime] = None
    sales_cycle_days: Optional[float] = None
    campaign_id: Optional[uuid.UUID] = None
    campaign_name: Optional[str] = None


class SnapshotCreateRequest(BaseModel):
    period_type: str = "ALL_TIME" # ALL_TIME, 30D, 90D, 180D, YTD, MONTHLY, CUSTOM
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    created_by: Optional[str] = "human_reviewer"


class SnapshotResponse(BaseModel):
    id: uuid.UUID
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    period_type: str
    reporting_currency: str
    total_realized_revenue: float
    total_open_pipeline_value: float
    weighted_pipeline_value: float
    total_recorded_costs: Optional[float] = None
    gross_profit: Optional[float] = None
    gross_margin_pct: Optional[float] = None
    deal_count_won: int
    deal_count_lost: int
    deal_count_open: int
    average_deal_size_won: Optional[float] = None
    average_sales_cycle_days: Optional[float] = None
    revenue_by_service: Optional[Dict[str, Any]] = None
    revenue_by_client: Optional[List[Dict[str, Any]]] = None
    revenue_by_campaign: Optional[List[Dict[str, Any]]] = None
    funnel_metrics: Optional[Dict[str, Any]] = None
    currency_breakdown: Optional[Dict[str, Any]] = None
    data_limitations: Optional[List[str]] = None
    created_at: datetime
    created_by: str

    model_config = ConfigDict(from_attributes=True)
