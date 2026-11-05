"""Add Super Admin and SEO Control Center models

Revision ID: g1a2b3c4d5e6
Revises: f1a2b3c4d5e6
Create Date: 2026-11-01 18:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'g1a2b3c4d5e6'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Platform Settings table
    op.create_table(
        'platform_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('key', sa.String(), nullable=False, unique=True),
        sa.Column('value', postgresql.JSONB(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_platform_settings_category', 'platform_settings', ['category'])
    op.create_index('ix_platform_settings_key', 'platform_settings', ['key'])

    # 2. Role Permissions table
    op.create_table(
        'role_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('role_name', sa.String(), nullable=False, unique=True),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('permissions', postgresql.JSONB(), nullable=False),
        sa.Column('is_system_role', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_role_permissions_role_name', 'role_permissions', ['role_name'])

    # 3. SEO Global Config table
    op.create_table(
        'seo_global_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('site_name', sa.String(), nullable=False, server_default='ProspectOS'),
        sa.Column('default_meta_title', sa.String(), nullable=False),
        sa.Column('default_meta_description', sa.Text(), nullable=False),
        sa.Column('default_canonical_domain', sa.String(), nullable=False),
        sa.Column('default_og_image_url', sa.String(), nullable=True),
        sa.Column('robots_txt_content', sa.Text(), nullable=True),
        sa.Column('sitemap_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('gsc_verification_code', sa.String(), nullable=True),
        sa.Column('ga4_measurement_id', sa.String(), nullable=True),
        sa.Column('bing_verification_code', sa.String(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 4. SEO Public Pages table
    op.create_table(
        'seo_public_pages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('path', sa.String(), nullable=False, unique=True),
        sa.Column('page_name', sa.String(), nullable=False),
        sa.Column('meta_title', sa.String(), nullable=False),
        sa.Column('meta_description', sa.Text(), nullable=False),
        sa.Column('canonical_url', sa.String(), nullable=False),
        sa.Column('og_title', sa.String(), nullable=True),
        sa.Column('og_description', sa.Text(), nullable=True),
        sa.Column('og_image_url', sa.String(), nullable=True),
        sa.Column('twitter_card', sa.String(), nullable=False, server_default='summary_large_image'),
        sa.Column('robots_directives', sa.String(), nullable=False, server_default='index,follow'),
        sa.Column('schema_type', sa.String(), nullable=False, server_default='SoftwareApplication'),
        sa.Column('structured_data_json', postgresql.JSONB(), nullable=True),
        sa.Column('sitemap_priority', sa.Float(), nullable=False, server_default='0.8'),
        sa.Column('change_frequency', sa.String(), nullable=False, server_default='weekly'),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_audited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('audit_score', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('audit_issues', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_seo_public_pages_path', 'seo_public_pages', ['path'])

    # 5. AI Provider Settings table
    op.create_table(
        'ai_provider_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('provider_name', sa.String(), nullable=False, unique=True),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('default_model', sa.String(), nullable=False),
        sa.Column('available_models', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('api_key_masked', sa.String(), nullable=True),
        sa.Column('api_key_encrypted', sa.String(), nullable=True),
        sa.Column('rpm_limit', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('tpm_limit', sa.Integer(), nullable=False, server_default='100000'),
        sa.Column('tokens_used_today', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('estimated_cost_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('last_tested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('feature_flags', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_ai_provider_settings_provider_name', 'ai_provider_settings', ['provider_name'])


def downgrade():
    op.drop_table('ai_provider_settings')
    op.drop_table('seo_public_pages')
    op.drop_table('seo_global_configs')
    op.drop_table('role_permissions')
    op.drop_table('platform_settings')

