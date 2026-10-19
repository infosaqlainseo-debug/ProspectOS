"""Add Phase 3.4 Automated Reporting and Client Portal Models

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-10-11 14:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b8c9d0e1f2a3'
down_revision: Union[str, Sequence[str], None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. portal_users
    op.create_table(
        'portal_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False, server_default='CLIENT_USER'),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('email', name='uq_portal_users_email')
    )
    op.create_index(op.f('ix_portal_users_email'), 'portal_users', ['email'], unique=True)
    op.create_index(op.f('ix_portal_users_role'), 'portal_users', ['role'], unique=False)
    op.create_index(op.f('ix_portal_users_company_id'), 'portal_users', ['company_id'], unique=False)
    op.create_index(op.f('ix_portal_users_is_active'), 'portal_users', ['is_active'], unique=False)

    # 2. client_invitations
    op.create_table(
        'client_invitations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('invitation_token', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False, server_default='CLIENT_USER'),
        sa.Column('invited_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_users.id'), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='PENDING'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('invitation_token', name='uq_client_invitations_token')
    )
    op.create_index(op.f('ix_client_invitations_company_id'), 'client_invitations', ['company_id'], unique=False)
    op.create_index(op.f('ix_client_invitations_email'), 'client_invitations', ['email'], unique=False)
    op.create_index(op.f('ix_client_invitations_token'), 'client_invitations', ['invitation_token'], unique=True)
    op.create_index(op.f('ix_client_invitations_status'), 'client_invitations', ['status'], unique=False)

    # 3. client_reports
    op.create_table(
        'client_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('report_type', sa.String(), nullable=False, server_default='MONTHLY_PERFORMANCE'),
        sa.Column('reporting_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reporting_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='DRAFT'),
        sa.Column('approval_status', sa.String(), nullable=False, server_default='UNAPPROVED'),
        sa.Column('approved_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_users.id'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('branding', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('sections', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('summary_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('delivery_status', sa.String(), nullable=False, server_default='NOT_DELIVERED'),
        sa.Column('generated_by', sa.String(), nullable=False, server_default='manual_operator'),
        sa.Column('data_limitations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('export_formats', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index(op.f('ix_client_reports_company_id'), 'client_reports', ['company_id'], unique=False)
    op.create_index(op.f('ix_client_reports_report_type'), 'client_reports', ['report_type'], unique=False)
    op.create_index(op.f('ix_client_reports_status'), 'client_reports', ['status'], unique=False)
    op.create_index(op.f('ix_client_reports_approval_status'), 'client_reports', ['approval_status'], unique=False)

    # 4. report_schedules
    op.create_table(
        'report_schedules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('report_type', sa.String(), nullable=False, server_default='MONTHLY_PERFORMANCE'),
        sa.Column('frequency', sa.String(), nullable=False, server_default='MONTHLY'),
        sa.Column('day_of_month', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('day_of_week', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('time_of_day', sa.String(), nullable=False, server_default='09:00'),
        sa.Column('time_zone', sa.String(), nullable=False, server_default='UTC'),
        sa.Column('recipients', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('requires_approval', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('last_generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index(op.f('ix_report_schedules_company_id'), 'report_schedules', ['company_id'], unique=False)
    op.create_index(op.f('ix_report_schedules_is_active'), 'report_schedules', ['is_active'], unique=False)

    # 5. report_delivery_logs
    op.create_table(
        'report_delivery_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_reports.id'), nullable=False),
        sa.Column('recipient_email', sa.String(), nullable=False),
        sa.Column('delivery_channel', sa.String(), nullable=False, server_default='EMAIL'),
        sa.Column('idempotency_key', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='PENDING'),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('idempotency_key', name='uq_report_delivery_idempotency')
    )
    op.create_index(op.f('ix_report_delivery_logs_report_id'), 'report_delivery_logs', ['report_id'], unique=False)
    op.create_index(op.f('ix_report_delivery_logs_recipient_email'), 'report_delivery_logs', ['recipient_email'], unique=False)
    op.create_index(op.f('ix_report_delivery_logs_idempotency_key'), 'report_delivery_logs', ['idempotency_key'], unique=True)
    op.create_index(op.f('ix_report_delivery_logs_status'), 'report_delivery_logs', ['status'], unique=False)

    # 6. portal_audit_logs
    op.create_table(
        'portal_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_users.id'), nullable=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index(op.f('ix_portal_audit_logs_user_id'), 'portal_audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_portal_audit_logs_company_id'), 'portal_audit_logs', ['company_id'], unique=False)
    op.create_index(op.f('ix_portal_audit_logs_action'), 'portal_audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_portal_audit_logs_timestamp'), 'portal_audit_logs', ['timestamp'], unique=False)


def downgrade() -> None:
    op.drop_table('portal_audit_logs')
    op.drop_table('report_delivery_logs')
    op.drop_table('report_schedules')
    op.drop_table('client_reports')
    op.drop_table('client_invitations')
    op.drop_table('portal_users')
