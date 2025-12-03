"""Add extraction and parsing fields to candidates table

Revision ID: 005
Revises: 004
Create Date: 2025-11-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Add extraction and parsing fields to candidates table
    # Note: match_score and reasoning already exist from migration 003
    op.add_column('candidates', sa.Column('extraction_status', sa.String(20), nullable=False, server_default='pending'))
    op.add_column('candidates', sa.Column('extracted_text', sa.Text(), nullable=True))
    op.add_column('candidates', sa.Column('parsed_name', sa.String(255), nullable=True))
    op.add_column('candidates', sa.Column('parsed_email', sa.String(255), nullable=True))
    op.add_column('candidates', sa.Column('parsed_phone', sa.String(50), nullable=True))
    op.add_column('candidates', sa.Column('parsed_skills', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('candidates', sa.Column('extraction_error', sa.Text(), nullable=True))
    op.add_column('candidates', sa.Column('extraction_duration', sa.Float(), nullable=True))
    op.add_column('candidates', sa.Column('file_size', sa.Integer(), nullable=True))
    op.add_column('candidates', sa.Column('file_type', sa.String(100), nullable=True))


def downgrade():
    op.drop_column('candidates', 'file_type')
    op.drop_column('candidates', 'file_size')
    op.drop_column('candidates', 'extraction_duration')
    op.drop_column('candidates', 'extraction_error')
    op.drop_column('candidates', 'parsed_skills')
    op.drop_column('candidates', 'parsed_phone')
    op.drop_column('candidates', 'parsed_email')
    op.drop_column('candidates', 'parsed_name')
    op.drop_column('candidates', 'extracted_text')
    op.drop_column('candidates', 'extraction_status')
