"""Add Phase 2.4 Outreach Automation Models

Revision ID: b2c3d4e5f6a7
Revises: a1c2d3e4f5a6
Create Date: 2026-10-10 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. company_contacts
    op.create_table(
        'company_contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('email', sa.String(), nullable=True, index=True),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('job_title', sa.String(), nullable=True),
        sa.Column('department', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('linkedin_url', sa.String(), nullable=True),
        sa.Column('source_type', sa.String(), nullable=False),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('retrieval_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('verification_status', sa.String(), nullable=False, server_default='UNVERIFIED'),
        sa.Column('confidence', sa.Float(), nullable=True, server_default='0.5'),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('opt_out', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('opt_out_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_company_contacts_company_id', 'company_contacts', ['company_id'])

    # 2. outreach_campaigns
    op.create_table(
        'outreach_campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='DRAFT'),
        sa.Column('daily_send_limit', sa.Integer(), nullable=False, server_default='20'),
        sa.Column('schedule_timezone', sa.String(), nullable=False, server_default='UTC'),
        sa.Column('follow_up_delay_days', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('max_follow_ups', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('stop_on_reply', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('stop_on_bounce', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('stop_on_unsubscribe', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('template_subject', sa.String(), nullable=True),
        sa.Column('template_body', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 3. outreach_drafts
    op.create_table(
        'outreach_drafts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('outreach_campaigns.id'), nullable=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company_contacts.id'), nullable=True),
        sa.Column('recipient_email', sa.String(), nullable=False),
        sa.Column('recipient_name', sa.String(), nullable=True),
        sa.Column('subject_line', sa.String(), nullable=False),
        sa.Column('body_text', sa.Text(), nullable=False),
        sa.Column('body_html', sa.Text(), nullable=True),
        sa.Column('call_to_action', sa.String(), nullable=True),
        sa.Column('prospect_summary', sa.Text(), nullable=True),
        sa.Column('evidence_citations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='DRAFT'),
        sa.Column('approval_status', sa.String(), nullable=False, server_default='UNAPPROVED'),
        sa.Column('approved_by', sa.String(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('is_follow_up', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sequence_step', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('parent_draft_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('outreach_drafts.id'), nullable=True),
        sa.Column('scheduled_send_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_outreach_drafts_company_id', 'outreach_drafts', ['company_id'])
    op.create_index('ix_outreach_drafts_recipient_email', 'outreach_drafts', ['recipient_email'])

    # 4. outreach_messages
    op.create_table(
        'outreach_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('draft_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('outreach_drafts.id'), nullable=False),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('outreach_campaigns.id'), nullable=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company_contacts.id'), nullable=True),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('provider_message_id', sa.String(), nullable=True),
        sa.Column('provider_thread_id', sa.String(), nullable=True),
        sa.Column('sender_email', sa.String(), nullable=False),
        sa.Column('recipient_email', sa.String(), nullable=False),
        sa.Column('subject_line', sa.String(), nullable=False),
        sa.Column('body_text', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='SENT'),
        sa.Column('delivery_error', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('replied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('bounced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('unsubscribed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_outreach_messages_company_id', 'outreach_messages', ['company_id'])
    op.create_index('ix_outreach_messages_recipient_email', 'outreach_messages', ['recipient_email'])

    # 5. outreach_suppressions
    op.create_table(
        'outreach_suppressions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(), nullable=False, unique=True),
        sa.Column('domain', sa.String(), nullable=True),
        sa.Column('reason', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_outreach_suppressions_email', 'outreach_suppressions', ['email'])
    op.create_index('ix_outreach_suppressions_domain', 'outreach_suppressions', ['domain'])


def downgrade() -> None:
    op.drop_table('outreach_suppressions')
    op.drop_table('outreach_messages')
    op.drop_table('outreach_drafts')
    op.drop_table('outreach_campaigns')
    op.drop_table('company_contacts')
