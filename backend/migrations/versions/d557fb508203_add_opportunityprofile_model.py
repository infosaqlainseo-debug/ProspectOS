"""Add OpportunityProfile model

Revision ID: d557fb508203
Revises: 87953192cb82
Create Date: 2026-10-09 12:09:10.597077

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd557fb508203'
down_revision: Union[str, Sequence[str], None] = '87953192cb82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('opportunity_profiles',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('company_id', sa.UUID(), nullable=False),
    sa.Column('recommended_service', sa.String(), nullable=False),
    sa.Column('opportunity_score', sa.Float(), nullable=False),
    sa.Column('supporting_evidence', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('identified_problems', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('confidence_level', sa.Float(), nullable=False),
    sa.Column('data_freshness', sa.String(), nullable=False),
    sa.Column('missing_information', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('recommended_next_action', sa.String(), nullable=True),
    sa.Column('methodology_version', sa.String(), nullable=False),
    sa.Column('calculation_timestamp', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('opportunity_profiles')
