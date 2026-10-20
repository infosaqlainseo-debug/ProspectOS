"""Add Phase 4.1 Google Drive and Social Outreach Models

Revision ID: c4d5e6f7a8b9
Revises: b8c9d0e1f2a3
Create Date: 2026-10-21 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, Sequence[str], None] = 'b8c9d0e1f2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add new columns to companies table
    op.add_column('companies', sa.Column('facebook_url', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('instagram_url', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('whatsapp_number', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('whatsapp_click_url', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('phone_number', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('public_email', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('contact_page_url', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('lead_priority', sa.String(), server_default='MEDIUM', nullable=False))
    op.add_column('companies', sa.Column('lead_score', sa.Float(), nullable=True))
    op.add_column('companies', sa.Column('lead_score_components', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('companies', sa.Column('recommended_services', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('companies', sa.Column('seo_summary_findings', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('companies', sa.Column('gdrive_file_id', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('gdrive_file_url', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('gdrive_synced_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('companies', sa.Column('gdrive_sync_status', sa.String(), server_default='NOT_SYNCED', nullable=False))
    op.add_column('companies', sa.Column('lead_owner', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('next_followup_date', sa.DateTime(timezone=True), nullable=True))

    # 2. google_drive_connections
    op.create_table(
        'google_drive_connections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('is_connected', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('account_email', sa.String(), nullable=True),
        sa.Column('access_token_encrypted', sa.Text(), nullable=True),
        sa.Column('refresh_token_encrypted', sa.Text(), nullable=True),
        sa.Column('token_expiry', sa.DateTime(timezone=True), nullable=True),
        sa.Column('client_id', sa.String(), nullable=True),
        sa.Column('client_secret_encrypted', sa.Text(), nullable=True),
        sa.Column('selected_folder_id', sa.String(), nullable=True),
        sa.Column('selected_folder_path', sa.String(), server_default='ProspectOS/Leads/', nullable=False),
        sa.Column('master_sheet_id', sa.String(), nullable=True),
        sa.Column('master_sheet_url', sa.String(), nullable=True),
        sa.Column('export_format', sa.String(), server_default='GOOGLE_SHEET', nullable=False),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_sync_status', sa.String(), server_default='IDLE', nullable=False),
        sa.Column('last_error_message', sa.Text(), nullable=True),
        sa.Column('auto_sync_enabled', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 3. google_drive_sync_jobs
    op.create_table(
        'google_drive_sync_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('status', sa.String(), server_default='PENDING', nullable=False),
        sa.Column('sync_type', sa.String(), server_default='AUTOMATIC', nullable=False),
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('resource_url', sa.String(), nullable=True),
        sa.Column('destination_folder', sa.String(), nullable=True),
        sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_google_drive_sync_jobs_company_id'), 'google_drive_sync_jobs', ['company_id'], unique=False)
    op.create_index(op.f('ix_google_drive_sync_jobs_status'), 'google_drive_sync_jobs', ['status'], unique=False)

    # 4. social_connections
    op.create_table(
        'social_connections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('account_name', sa.String(), nullable=True),
        sa.Column('account_id', sa.String(), nullable=True),
        sa.Column('phone_number', sa.String(), nullable=True),
        sa.Column('is_connected', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('permissions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('access_token_encrypted', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('messaging_enabled', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('last_successful_operation_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('configuration_error', sa.Text(), nullable=True),
        sa.Column('settings_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('channel', name='uq_social_connections_channel')
    )
    op.create_index(op.f('ix_social_connections_channel'), 'social_connections', ['channel'], unique=True)

    # 5. social_message_logs
    op.create_table(
        'social_message_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('company_contacts.id'), nullable=True),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('direction', sa.String(), server_default='OUTBOUND', nullable=False),
        sa.Column('recipient_identifier', sa.String(), nullable=False),
        sa.Column('sender_account', sa.String(), nullable=True),
        sa.Column('message_text', sa.Text(), nullable=False),
        sa.Column('template_name', sa.String(), nullable=True),
        sa.Column('status', sa.String(), server_default='PREPARED', nullable=False),
        sa.Column('api_message_id', sa.String(), nullable=True),
        sa.Column('click_to_chat_url', sa.Text(), nullable=True),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('explicit_user_confirmed', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_social_message_logs_company_id'), 'social_message_logs', ['company_id'], unique=False)
    op.create_index(op.f('ix_social_message_logs_channel'), 'social_message_logs', ['channel'], unique=False)
    op.create_index(op.f('ix_social_message_logs_status'), 'social_message_logs', ['status'], unique=False)


def downgrade() -> None:
    op.drop_table('social_message_logs')
    op.drop_table('social_connections')
    op.drop_table('google_drive_sync_jobs')
    op.drop_table('google_drive_connections')

    op.drop_column('companies', 'next_followup_date')
    op.drop_column('companies', 'lead_owner')
    op.drop_column('companies', 'gdrive_sync_status')
    op.drop_column('companies', 'gdrive_synced_at')
    op.drop_column('companies', 'gdrive_file_url')
    op.drop_column('companies', 'gdrive_file_id')
    op.drop_column('companies', 'seo_summary_findings')
    op.drop_column('companies', 'recommended_services')
    op.drop_column('companies', 'lead_score_components')
    op.drop_column('companies', 'lead_score')
    op.drop_column('companies', 'lead_priority')
    op.drop_column('companies', 'contact_page_url')
    op.drop_column('companies', 'public_email')
    op.drop_column('companies', 'phone_number')
    op.drop_column('companies', 'whatsapp_click_url')
    op.drop_column('companies', 'whatsapp_number')
    op.drop_column('companies', 'instagram_url')
    op.drop_column('companies', 'facebook_url')
