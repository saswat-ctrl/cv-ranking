"""create ranking_jobs table

Revision ID: 002
Revises: 001
Create Date: 2023-10-27 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # SQLAlchemy will automatically create the enum type when creating the table
    op.create_table('ranking_jobs',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('jd_file_url', sa.String(), nullable=False),
    sa.Column('jd_text_content', sa.Text(), nullable=True),
    sa.Column('job_title', sa.String(), nullable=True),
    sa.Column('status', sa.Enum('OPEN', 'CLOSED', 'ARCHIVED', 'UPLOADED', 'PROCESSING', 'READY', 'FAILED', name='jobstatus'), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ranking_jobs_id'), 'ranking_jobs', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ranking_jobs_id'), table_name='ranking_jobs')
    op.drop_table('ranking_jobs')
    # The enum type will be automatically dropped with the table

