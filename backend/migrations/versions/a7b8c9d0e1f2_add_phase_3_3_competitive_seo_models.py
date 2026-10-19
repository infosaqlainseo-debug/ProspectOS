"""Add Phase 3.3 Advanced Competitive SEO Intelligence Models

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-10-11 11:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, Sequence[str], None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. company_competitors
    op.create_table(
        'company_competitors',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('competitor_company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=True),
        sa.Column('competitor_name', sa.String(), nullable=False),
        sa.Column('competitor_domain', sa.String(), nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('relevance_tier', sa.String(), nullable=False, server_default='DIRECT'),
        sa.Column('validation_status', sa.String(), nullable=False, server_default='VERIFIED'),
        sa.Column('validation_evidence', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('discovery_method', sa.String(), nullable=False, server_default='INDUSTRY_TOPICAL_OVERLAP'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('company_id', 'competitor_domain', name='uq_company_competitor_domain')
    )
    op.create_index(op.f('ix_company_competitors_company_id'), 'company_competitors', ['company_id'], unique=False)
    op.create_index(op.f('ix_company_competitors_competitor_company_id'), 'company_competitors', ['competitor_company_id'], unique=False)
    op.create_index(op.f('ix_company_competitors_competitor_domain'), 'company_competitors', ['competitor_domain'], unique=False)

    # 2. competitive_analysis_runs
    op.create_table(
        'competitive_analysis_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('competitor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company_competitors.id'), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='COMPLETED'),
        sa.Column('prospect_scan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('website_scans.id'), nullable=True),
        sa.Column('competitor_scan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('website_scans.id'), nullable=True),
        sa.Column('summary_findings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('content_gaps', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('technical_gaps', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('internal_linking_gaps', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('backlink_gaps', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('publisher_opportunities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('prioritized_recommendations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('data_limitations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('analyzed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index(op.f('ix_competitive_analysis_runs_company_id'), 'competitive_analysis_runs', ['company_id'], unique=False)
    op.create_index(op.f('ix_competitive_analysis_runs_competitor_id'), 'competitive_analysis_runs', ['competitor_id'], unique=False)
    op.create_index(op.f('ix_competitive_analysis_runs_status'), 'competitive_analysis_runs', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_competitive_analysis_runs_status'), table_name='competitive_analysis_runs')
    op.drop_index(op.f('ix_competitive_analysis_runs_competitor_id'), table_name='competitive_analysis_runs')
    op.drop_index(op.f('ix_competitive_analysis_runs_company_id'), table_name='competitive_analysis_runs')
    op.drop_table('competitive_analysis_runs')

    op.drop_index(op.f('ix_company_competitors_competitor_domain'), table_name='company_competitors')
    op.drop_index(op.f('ix_company_competitors_competitor_company_id'), table_name='company_competitors')
    op.drop_index(op.f('ix_company_competitors_company_id'), table_name='company_competitors')
    op.drop_table('company_competitors')
