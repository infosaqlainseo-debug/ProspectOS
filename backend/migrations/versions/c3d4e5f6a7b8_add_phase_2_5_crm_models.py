"""Add Phase 2.5 CRM & Sales Pipeline Models

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-10-10 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enhance companies table with sales pipeline fields
    op.add_column('companies', sa.Column('sales_stage', sa.String(), nullable=False, server_default='NEW'))
    op.create_index(op.f('ix_companies_sales_stage'), 'companies', ['sales_stage'], unique=False)
    op.add_column('companies', sa.Column('target_market', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('qualification_notes', sa.Text(), nullable=True))
    op.add_column('companies', sa.Column('stage_updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column('companies', sa.Column('stage_reason', sa.String(), nullable=True))

    # 2. crm_deals
    op.create_table(
        'crm_deals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company_contacts.id'), nullable=True),
        sa.Column('deal_name', sa.String(), nullable=False),
        sa.Column('service_category', sa.String(), nullable=False, server_default='FULL_SERVICE'),
        sa.Column('stage', sa.String(), nullable=False, server_default='DISCOVERY'),
        sa.Column('estimated_value', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('proposed_value', sa.Float(), nullable=True),
        sa.Column('closed_amount', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('expected_close_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_close_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('outcome', sa.String(), nullable=True),
        sa.Column('loss_reason', sa.String(), nullable=True),
        sa.Column('win_reason', sa.String(), nullable=True),
        sa.Column('media_plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('media_plans.id'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index(op.f('ix_crm_deals_company_id'), 'crm_deals', ['company_id'], unique=False)
    op.create_index(op.f('ix_crm_deals_stage'), 'crm_deals', ['stage'], unique=False)

    # 3. crm_tasks
    op.create_table(
        'crm_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company_contacts.id'), nullable=True),
        sa.Column('deal_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('crm_deals.id'), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('task_type', sa.String(), nullable=False, server_default='FOLLOW_UP'),
        sa.Column('priority', sa.String(), nullable=False, server_default='MEDIUM'),
        sa.Column('status', sa.String(), nullable=False, server_default='PENDING'),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_by', sa.String(), nullable=True),
        sa.Column('completion_notes', sa.Text(), nullable=True),
        sa.Column('idempotency_key', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index(op.f('ix_crm_tasks_company_id'), 'crm_tasks', ['company_id'], unique=False)
    op.create_index(op.f('ix_crm_tasks_status'), 'crm_tasks', ['status'], unique=False)
    op.create_index(op.f('ix_crm_tasks_due_date'), 'crm_tasks', ['due_date'], unique=False)
    op.create_index(op.f('ix_crm_tasks_idempotency_key'), 'crm_tasks', ['idempotency_key'], unique=False)

    # 4. crm_activities
    op.create_table(
        'crm_activities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('deal_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('crm_deals.id'), nullable=True),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company_contacts.id'), nullable=True),
        sa.Column('activity_type', sa.String(), nullable=False),
        sa.Column('actor', sa.String(), nullable=False, server_default='human_reviewer'),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index(op.f('ix_crm_activities_company_id'), 'crm_activities', ['company_id'], unique=False)
    op.create_index(op.f('ix_crm_activities_created_at'), 'crm_activities', ['created_at'], unique=False)

    # 5. crm_notes
    op.create_table(
        'crm_notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('deal_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('crm_deals.id'), nullable=True),
        sa.Column('author', sa.String(), nullable=False, server_default='human_reviewer'),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index(op.f('ix_crm_notes_company_id'), 'crm_notes', ['company_id'], unique=False)


def downgrade() -> None:
    op.drop_table('crm_notes')
    op.drop_table('crm_activities')
    op.drop_table('crm_tasks')
    op.drop_table('crm_deals')
    op.drop_index(op.f('ix_companies_sales_stage'), table_name='companies')
    op.drop_column('companies', 'stage_reason')
    op.drop_column('companies', 'stage_updated_at')
    op.drop_column('companies', 'qualification_notes')
    op.drop_column('companies', 'target_market')
    op.drop_column('companies', 'sales_stage')
