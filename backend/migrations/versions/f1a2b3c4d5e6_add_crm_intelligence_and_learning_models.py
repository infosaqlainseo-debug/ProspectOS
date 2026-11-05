"""Add CRM intelligence and adaptive learning models

Revision ID: f1a2b3c4d5e6
Revises: e1f2a3b4c5d6
Create Date: 2026-10-31 22:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add enriched CRM columns to companies
    op.add_column('companies', sa.Column('lead_source', sa.String(), server_default='SCRAPER', nullable=True))
    op.add_column('companies', sa.Column('source_task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('scraper_tasks.id', ondelete='SET NULL'), nullable=True))
    op.add_column('companies', sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=True))
    op.add_column('companies', sa.Column('custom_fields', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True))
    op.add_column('companies', sa.Column('company_size', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('contact_person', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('contact_title', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('linkedin_url', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('domain_rating', sa.Float(), nullable=True))
    op.add_column('companies', sa.Column('domain_authority', sa.Float(), nullable=True))
    op.add_column('companies', sa.Column('organic_traffic', sa.Float(), nullable=True))
    op.add_column('companies', sa.Column('website_status', sa.String(), server_default='ACTIVE', nullable=True))
    op.add_column('companies', sa.Column('technology_stack', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=True))
    op.add_column('companies', sa.Column('data_verification_status', sa.String(), server_default='VERIFIED', nullable=True))

    # 2. CRM Lead Segments
    op.create_table(
        'crm_lead_segments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_dynamic', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('filter_criteria', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('color', sa.String(), server_default='blue', nullable=False),
        sa.Column('icon', sa.String(), nullable=True),
        sa.Column('member_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_crm_lead_segments_name'), 'crm_lead_segments', ['name'], unique=False)
    op.create_index(op.f('ix_crm_lead_segments_created_at'), 'crm_lead_segments', ['created_at'], unique=False)

    # 3. CRM Segment Members (for static lists)
    op.create_table(
        'crm_segment_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('segment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('crm_lead_segments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_crm_segment_members_segment_id'), 'crm_segment_members', ['segment_id'], unique=False)
    op.create_index(op.f('ix_crm_segment_members_company_id'), 'crm_segment_members', ['company_id'], unique=False)

    # 4. CRM User Preferences (for adaptive AI learning)
    op.create_table(
        'crm_user_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(), server_default='default_user', nullable=False),
        sa.Column('preferred_industries', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('preferred_countries', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('min_lead_score', sa.Float(), server_default='50.0', nullable=False),
        sa.Column('scoring_weights', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('target_market_rules', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_crm_user_preferences_user_id'), 'crm_user_preferences', ['user_id'], unique=True)

    # 5. CRM Feedback Logs
    op.create_table(
        'crm_feedback_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action_taken', sa.String(), nullable=False),
        sa.Column('previous_stage', sa.String(), nullable=True),
        sa.Column('new_stage', sa.String(), nullable=True),
        sa.Column('previous_score', sa.Float(), nullable=True),
        sa.Column('new_score', sa.Float(), nullable=True),
        sa.Column('feedback_reason', sa.Text(), nullable=True),
        sa.Column('actor', sa.String(), server_default='human_reviewer', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_crm_feedback_logs_company_id'), 'crm_feedback_logs', ['company_id'], unique=False)
    op.create_index(op.f('ix_crm_feedback_logs_action_taken'), 'crm_feedback_logs', ['action_taken'], unique=False)
    op.create_index(op.f('ix_crm_feedback_logs_created_at'), 'crm_feedback_logs', ['created_at'], unique=False)

    # 6. CRM AI Research ("Analyze with AI")
    op.create_table(
        'crm_ai_research',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('executive_summary', sa.Text(), nullable=True),
        sa.Column('target_market', sa.Text(), nullable=True),
        sa.Column('value_proposition', sa.Text(), nullable=True),
        sa.Column('seo_weaknesses', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('backlink_opportunities', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('recommended_services', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('growth_opportunities', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('tech_stack_detected', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('confidence_score', sa.Float(), server_default='0.85', nullable=False),
        sa.Column('model_used', sa.String(), server_default='gemini-2.5-pro', nullable=False),
        sa.Column('analyzed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_crm_ai_research_company_id'), 'crm_ai_research', ['company_id'], unique=True)

    # 7. CRM Custom Fields
    op.create_table(
        'crm_custom_fields',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('field_key', sa.String(), nullable=False),
        sa.Column('field_value', sa.Text(), nullable=True),
        sa.Column('field_type', sa.String(), server_default='TEXT', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_crm_custom_fields_company_id'), 'crm_custom_fields', ['company_id'], unique=False)
    op.create_index(op.f('ix_crm_custom_fields_field_key'), 'crm_custom_fields', ['field_key'], unique=False)


def downgrade() -> None:
    op.drop_table('crm_custom_fields')
    op.drop_table('crm_ai_research')
    op.drop_table('crm_feedback_logs')
    op.drop_table('crm_user_preferences')
    op.drop_table('crm_segment_members')
    op.drop_table('crm_lead_segments')

    op.drop_column('companies', 'data_verification_status')
    op.drop_column('companies', 'technology_stack')
    op.drop_column('companies', 'website_status')
    op.drop_column('companies', 'organic_traffic')
    op.drop_column('companies', 'domain_authority')
    op.drop_column('companies', 'domain_rating')
    op.drop_column('companies', 'linkedin_url')
    op.drop_column('companies', 'contact_title')
    op.drop_column('companies', 'contact_person')
    op.drop_column('companies', 'company_size')
    op.drop_column('companies', 'custom_fields')
    op.drop_column('companies', 'tags')
    op.drop_column('companies', 'source_task_id')
    op.drop_column('companies', 'lead_source')

