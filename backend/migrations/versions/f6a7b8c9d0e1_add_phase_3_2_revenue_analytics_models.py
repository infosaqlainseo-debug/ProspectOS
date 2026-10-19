"""Add Phase 3.2 Revenue Analytics Models and CRM Deal Financial Fields

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-10-11 10:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add financial and attribution columns to crm_deals
    op.add_column('crm_deals', sa.Column('campaign_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('outreach_campaigns.id'), nullable=True))
    op.create_index(op.f('ix_crm_deals_campaign_id'), 'crm_deals', ['campaign_id'], unique=False)
    op.add_column('crm_deals', sa.Column('cost_amount', sa.Float(), nullable=True))
    op.add_column('crm_deals', sa.Column('invoice_status', sa.String(), nullable=True))
    op.add_column('crm_deals', sa.Column('invoiced_amount', sa.Float(), nullable=True))
    op.add_column('crm_deals', sa.Column('paid_amount', sa.Float(), nullable=True))
    op.add_column('crm_deals', sa.Column('discount_amount', sa.Float(), server_default='0.0', nullable=True))
    op.add_column('crm_deals', sa.Column('tax_amount', sa.Float(), server_default='0.0', nullable=True))
    op.add_column('crm_deals', sa.Column('refunded_amount', sa.Float(), server_default='0.0', nullable=True))

    # 2. Create revenue_analytics_snapshots table
    op.create_table(
        'revenue_analytics_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_type', sa.String(), nullable=False, server_default='ALL_TIME'),
        sa.Column('reporting_currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('total_realized_revenue', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_open_pipeline_value', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('weighted_pipeline_value', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_recorded_costs', sa.Float(), nullable=True),
        sa.Column('gross_profit', sa.Float(), nullable=True),
        sa.Column('gross_margin_pct', sa.Float(), nullable=True),
        sa.Column('deal_count_won', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('deal_count_lost', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('deal_count_open', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_deal_size_won', sa.Float(), nullable=True),
        sa.Column('average_sales_cycle_days', sa.Float(), nullable=True),
        sa.Column('revenue_by_service', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('revenue_by_client', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('revenue_by_campaign', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('funnel_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('currency_breakdown', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('data_limitations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False, server_default='system')
    )
    op.create_index(op.f('ix_revenue_analytics_snapshots_period_type'), 'revenue_analytics_snapshots', ['period_type'], unique=False)
    op.create_index(op.f('ix_revenue_analytics_snapshots_created_at'), 'revenue_analytics_snapshots', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_revenue_analytics_snapshots_created_at'), table_name='revenue_analytics_snapshots')
    op.drop_index(op.f('ix_revenue_analytics_snapshots_period_type'), table_name='revenue_analytics_snapshots')
    op.drop_table('revenue_analytics_snapshots')

    op.drop_column('crm_deals', 'refunded_amount')
    op.drop_column('crm_deals', 'tax_amount')
    op.drop_column('crm_deals', 'discount_amount')
    op.drop_column('crm_deals', 'paid_amount')
    op.drop_column('crm_deals', 'invoiced_amount')
    op.drop_column('crm_deals', 'invoice_status')
    op.drop_column('crm_deals', 'cost_amount')
    op.drop_index(op.f('ix_crm_deals_campaign_id'), table_name='crm_deals')
    op.drop_column('crm_deals', 'campaign_id')
