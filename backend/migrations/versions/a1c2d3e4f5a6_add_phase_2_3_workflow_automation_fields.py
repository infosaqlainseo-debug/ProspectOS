"""Add Phase 2.3 Workflow Automation Fields

Revision ID: a1c2d3e4f5a6
Revises: 96dc5e273222
Create Date: 2026-10-10 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = '96dc5e273222'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to workflows
    op.add_column('workflows', sa.Column('selected_company_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('workflows', sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True))

    # Add new columns to workflow_runs
    op.add_column('workflow_runs', sa.Column('stage_progress', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('workflow_runs', sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('workflow_runs', sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('workflow_runs', sa.Column('approved_by', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('workflow_runs', 'approved_by')
    op.drop_column('workflow_runs', 'approved_at')
    op.drop_column('workflow_runs', 'parameters')
    op.drop_column('workflow_runs', 'stage_progress')
    op.drop_column('workflows', 'last_run_at')
    op.drop_column('workflows', 'selected_company_ids')
