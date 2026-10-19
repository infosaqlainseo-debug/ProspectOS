"""add_seo_enrichment_fields

Revision ID: 76842081ba71
Revises: 5af30d17b3f1
Create Date: 2026-10-08 21:41:18.445213

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '76842081ba71'
down_revision: Union[str, Sequence[str], None] = '5af30d17b3f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add fields to jobs
    op.add_column('jobs', sa.Column('processed_count', sa.Integer(), nullable=True))
    op.add_column('jobs', sa.Column('successful_count', sa.Integer(), nullable=True))
    op.add_column('jobs', sa.Column('partial_count', sa.Integer(), nullable=True))
    op.add_column('jobs', sa.Column('provider_error_count', sa.Integer(), nullable=True))
    op.add_column('jobs', sa.Column('metrics_created', sa.Integer(), nullable=True))
    op.add_column('jobs', sa.Column('metrics_skipped', sa.Integer(), nullable=True))

    # Add fields to seo_metrics
    op.add_column('seo_metrics', sa.Column('domain', sa.String(), nullable=True))
    op.add_column('seo_metrics', sa.Column('provider_metric_name', sa.String(), nullable=True))
    op.add_column('seo_metrics', sa.Column('provider_endpoint', sa.String(), nullable=True))
    op.add_column('seo_metrics', sa.Column('request_id', sa.String(), nullable=True))

    # Create provider_usage table
    op.create_table('provider_usage',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('job_id', sa.UUID(), nullable=True),
        sa.Column('company_id', sa.UUID(), nullable=True),
        sa.Column('request_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('estimated_units', sa.Float(), nullable=True),
        sa.Column('actual_units', sa.Float(), nullable=True),
        sa.Column('endpoint', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('provider_usage')
    
    op.drop_column('seo_metrics', 'request_id')
    op.drop_column('seo_metrics', 'provider_endpoint')
    op.drop_column('seo_metrics', 'provider_metric_name')
    op.drop_column('seo_metrics', 'domain')

    op.drop_column('jobs', 'metrics_skipped')
    op.drop_column('jobs', 'metrics_created')
    op.drop_column('jobs', 'provider_error_count')
    op.drop_column('jobs', 'partial_count')
    op.drop_column('jobs', 'successful_count')
    op.drop_column('jobs', 'processed_count')
