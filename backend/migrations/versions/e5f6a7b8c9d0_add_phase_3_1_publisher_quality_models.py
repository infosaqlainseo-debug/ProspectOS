"""Add Phase 3.1 Publisher Quality and Monitoring Models

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-10-11 10:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. publisher_quality_scores
    op.create_table(
        'publisher_quality_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('publisher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('publisher_records.id'), nullable=False),
        sa.Column('overall_quality_score', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('completeness_score', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('freshness_score', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('validity_score', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('consistency_score', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('price_freshness_status', sa.String(), nullable=False, server_default='UNKNOWN'),
        sa.Column('metrics_freshness_status', sa.String(), nullable=False, server_default='UNKNOWN'),
        sa.Column('site_freshness_status', sa.String(), nullable=False, server_default='UNKNOWN'),
        sa.Column('last_price_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_metrics_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_site_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('open_issues_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('critical_issues_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('has_duplicates', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('has_conflicts', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('last_audited_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index(op.f('ix_publisher_quality_scores_publisher_id'), 'publisher_quality_scores', ['publisher_id'], unique=True)
    op.create_index(op.f('ix_publisher_quality_scores_overall_quality_score'), 'publisher_quality_scores', ['overall_quality_score'], unique=False)

    # 2. publisher_quality_findings
    op.create_table(
        'publisher_quality_findings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('publisher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('publisher_records.id'), nullable=False),
        sa.Column('issue_type', sa.String(), nullable=False),
        sa.Column('field_name', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False, server_default='MEDIUM'),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('evidence', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('recommended_action', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='OPEN'),
        sa.Column('resolution_action', sa.String(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolved_by', sa.String(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index(op.f('ix_publisher_quality_findings_publisher_id'), 'publisher_quality_findings', ['publisher_id'], unique=False)
    op.create_index(op.f('ix_publisher_quality_findings_issue_type'), 'publisher_quality_findings', ['issue_type'], unique=False)
    op.create_index(op.f('ix_publisher_quality_findings_severity'), 'publisher_quality_findings', ['severity'], unique=False)
    op.create_index(op.f('ix_publisher_quality_findings_status'), 'publisher_quality_findings', ['status'], unique=False)

    # 3. publisher_refresh_logs
    op.create_table(
        'publisher_refresh_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('publisher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('publisher_records.id'), nullable=False),
        sa.Column('target_field', sa.String(), nullable=False),
        sa.Column('provider_attempted', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('initiated_by', sa.String(), nullable=False, server_default='system_audit'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index(op.f('ix_publisher_refresh_logs_publisher_id'), 'publisher_refresh_logs', ['publisher_id'], unique=False)
    op.create_index(op.f('ix_publisher_refresh_logs_status'), 'publisher_refresh_logs', ['status'], unique=False)


def downgrade() -> None:
    op.drop_table('publisher_refresh_logs')
    op.drop_table('publisher_quality_findings')
    op.drop_table('publisher_quality_scores')
