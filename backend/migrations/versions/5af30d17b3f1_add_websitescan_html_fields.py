"""Add WebsiteScan HTML fields

Revision ID: 5af30d17b3f1
Revises: 372d960c6eb0
Create Date: 2026-10-08 21:05:53.206528

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5af30d17b3f1'
down_revision: Union[str, Sequence[str], None] = '372d960c6eb0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from sqlalchemy.dialects import postgresql

def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('website_scans', sa.Column('robots_meta', sa.String(), nullable=True))
    op.add_column('website_scans', sa.Column('viewport', sa.String(), nullable=True))
    op.add_column('website_scans', sa.Column('language', sa.String(), nullable=True))
    op.add_column('website_scans', sa.Column('charset', sa.String(), nullable=True))
    op.add_column('website_scans', sa.Column('h1', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('website_scans', sa.Column('h2', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('website_scans', sa.Column('open_graph', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('website_scans', sa.Column('twitter_card', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('website_scans', sa.Column('error_message', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('website_scans', 'error_message')
    op.drop_column('website_scans', 'twitter_card')
    op.drop_column('website_scans', 'open_graph')
    op.drop_column('website_scans', 'h2')
    op.drop_column('website_scans', 'h1')
    op.drop_column('website_scans', 'charset')
    op.drop_column('website_scans', 'language')
    op.drop_column('website_scans', 'viewport')
    op.drop_column('website_scans', 'robots_meta')
