"""Add Phase 3.0 Sales Intelligence & Lead Prioritization Models

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-10-11 00:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. sales_intelligence_scores
    op.create_table(
        'sales_intelligence_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('scoring_version', sa.String(), nullable=False, server_default='v3.0.0'),
        sa.Column('overall_priority_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('seo_severity_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('service_fit_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('publisher_fit_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('business_fit_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('evidence_confidence_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('data_completeness', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('primary_recommended_service', sa.String(), nullable=True),
        sa.Column('recommended_services', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('positive_indicators', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('limitations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('missing_information', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('component_weights', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('recommended_next_action', sa.String(), nullable=True),
        sa.Column('review_status', sa.String(), nullable=False, server_default='UNREVIEWED'),
        sa.Column('human_override_score', sa.Float(), nullable=True),
        sa.Column('human_override_reason', sa.String(), nullable=True),
        sa.Column('human_override_by', sa.String(), nullable=True),
        sa.Column('human_override_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index(op.f('ix_sales_intelligence_scores_company_id'), 'sales_intelligence_scores', ['company_id'], unique=True)
    op.create_index(op.f('ix_sales_intelligence_scores_review_status'), 'sales_intelligence_scores', ['review_status'], unique=False)
    op.create_index(op.f('ix_sales_intelligence_scores_overall_priority_score'), 'sales_intelligence_scores', ['overall_priority_score'], unique=False)

    # 2. sales_opportunities
    op.create_table(
        'sales_opportunities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False, server_default='MEDIUM'),
        sa.Column('impact_rationale', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('recommended_service', sa.String(), nullable=False),
        sa.Column('supporting_evidence', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='ACTIVE'),
        sa.Column('detection_rule', sa.String(), nullable=False),
        sa.Column('detection_timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index(op.f('ix_sales_opportunities_company_id'), 'sales_opportunities', ['company_id'], unique=False)
    op.create_index(op.f('ix_sales_opportunities_category'), 'sales_opportunities', ['category'], unique=False)
    op.create_index(op.f('ix_sales_opportunities_severity'), 'sales_opportunities', ['severity'], unique=False)
    op.create_index(op.f('ix_sales_opportunities_status'), 'sales_opportunities', ['status'], unique=False)

    # 3. sales_briefs
    op.create_table(
        'sales_briefs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('company_overview', sa.Text(), nullable=False),
        sa.Column('seo_findings_summary', sa.Text(), nullable=False),
        sa.Column('top_opportunities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('recommended_services', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('matched_publishers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('data_gaps', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('discovery_questions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('recommended_next_action', sa.String(), nullable=True),
        sa.Column('full_brief_markdown', sa.Text(), nullable=False),
        sa.Column('is_customized', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('last_edited_by', sa.String(), nullable=True),
        sa.Column('last_edited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index(op.f('ix_sales_briefs_company_id'), 'sales_briefs', ['company_id'], unique=True)


def downgrade() -> None:
    op.drop_table('sales_briefs')
    op.drop_table('sales_opportunities')
    op.drop_table('sales_intelligence_scores')
