"""Add ProspectOS Scraper models

Revision ID: e1f2a3b4c5d6
Revises: c4d5e6f7a8b9
Create Date: 2026-10-31 21:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, Sequence[str], None] = 'c4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Scraper Tasks
    op.create_table(
        'scraper_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('task_type', sa.String(), server_default='CUSTOM', nullable=False),
        sa.Column('template_id', sa.String(), nullable=True),
        sa.Column('target_url', sa.String(), nullable=True),
        sa.Column('workflow_config', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('execution_mode', sa.String(), server_default='CLOUD', nullable=False),
        sa.Column('status', sa.String(), server_default='DRAFT', nullable=False),
        sa.Column('schedule_type', sa.String(), server_default='NONE', nullable=False),
        sa.Column('schedule_cron', sa.String(), nullable=True),
        sa.Column('schedule_timezone', sa.String(), server_default='UTC', nullable=False),
        sa.Column('is_schedule_active', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_records', sa.Integer(), server_default='0', nullable=False),
        sa.Column('successful_records', sa.Integer(), server_default='0', nullable=False),
        sa.Column('failed_records', sa.Integer(), server_default='0', nullable=False),
        sa.Column('duplicate_records', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_scraper_tasks_name'), 'scraper_tasks', ['name'], unique=False)
    op.create_index(op.f('ix_scraper_tasks_task_type'), 'scraper_tasks', ['task_type'], unique=False)
    op.create_index(op.f('ix_scraper_tasks_template_id'), 'scraper_tasks', ['template_id'], unique=False)
    op.create_index(op.f('ix_scraper_tasks_status'), 'scraper_tasks', ['status'], unique=False)
    op.create_index(op.f('ix_scraper_tasks_created_at'), 'scraper_tasks', ['created_at'], unique=False)

    # 2. Scraper Task Runs
    op.create_table(
        'scraper_task_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('scraper_tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('run_number', sa.Integer(), server_default='1', nullable=False),
        sa.Column('execution_mode', sa.String(), server_default='CLOUD', nullable=False),
        sa.Column('status', sa.String(), server_default='QUEUED', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('records_extracted', sa.Integer(), server_default='0', nullable=False),
        sa.Column('records_saved', sa.Integer(), server_default='0', nullable=False),
        sa.Column('records_duplicate', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('logs', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_scraper_task_runs_task_id'), 'scraper_task_runs', ['task_id'], unique=False)
    op.create_index(op.f('ix_scraper_task_runs_status'), 'scraper_task_runs', ['status'], unique=False)
    op.create_index(op.f('ix_scraper_task_runs_created_at'), 'scraper_task_runs', ['created_at'], unique=False)

    # 3. Extracted Records
    op.create_table(
        'extracted_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('scraper_tasks.id', ondelete='SET NULL'), nullable=True),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('scraper_task_runs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('record_hash', sa.String(), nullable=False),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('cleaned_data', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('company_name', sa.String(), nullable=True),
        sa.Column('website', sa.String(), nullable=True),
        sa.Column('domain', sa.String(), nullable=True),
        sa.Column('industry', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('country', sa.String(), nullable=True),
        sa.Column('city', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('social_profiles', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('discovery_source', sa.String(), server_default='SCRAPER', nullable=False),
        sa.Column('validation_status', sa.String(), server_default='VALID', nullable=False),
        sa.Column('quality_score', sa.Float(), server_default='100.0', nullable=False),
        sa.Column('quality_status', sa.String(), server_default='HIGH', nullable=False),
        sa.Column('validation_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_duplicate', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_extracted_records_task_id'), 'extracted_records', ['task_id'], unique=False)
    op.create_index(op.f('ix_extracted_records_run_id'), 'extracted_records', ['run_id'], unique=False)
    op.create_index(op.f('ix_extracted_records_record_hash'), 'extracted_records', ['record_hash'], unique=False)
    op.create_index(op.f('ix_extracted_records_company_name'), 'extracted_records', ['company_name'], unique=False)
    op.create_index(op.f('ix_extracted_records_domain'), 'extracted_records', ['domain'], unique=False)
    op.create_index(op.f('ix_extracted_records_industry'), 'extracted_records', ['industry'], unique=False)
    op.create_index(op.f('ix_extracted_records_country'), 'extracted_records', ['country'], unique=False)
    op.create_index(op.f('ix_extracted_records_discovery_source'), 'extracted_records', ['discovery_source'], unique=False)
    op.create_index(op.f('ix_extracted_records_validation_status'), 'extracted_records', ['validation_status'], unique=False)
    op.create_index(op.f('ix_extracted_records_is_duplicate'), 'extracted_records', ['is_duplicate'], unique=False)
    op.create_index(op.f('ix_extracted_records_created_at'), 'extracted_records', ['created_at'], unique=False)

    # 4. Export Jobs
    op.create_table(
        'export_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('scraper_tasks.id', ondelete='SET NULL'), nullable=True),
        sa.Column('format', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), server_default='0', nullable=False),
        sa.Column('record_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('filter_criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(), server_default='PENDING', nullable=False),
        sa.Column('download_url', sa.String(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_export_jobs_task_id'), 'export_jobs', ['task_id'], unique=False)
    op.create_index(op.f('ix_export_jobs_created_at'), 'export_jobs', ['created_at'], unique=False)

    # 5. Scraper API Keys
    op.create_table(
        'scraper_api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('key_hash', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('prefix', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('rate_limit_rpm', sa.Integer(), server_default='60', nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_scraper_api_keys_key_hash'), 'scraper_api_keys', ['key_hash'], unique=True)


def downgrade() -> None:
    op.drop_table('scraper_api_keys')
    op.drop_table('export_jobs')
    op.drop_table('extracted_records')
    op.drop_table('scraper_task_runs')
    op.drop_table('scraper_tasks')

