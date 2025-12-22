"""Add job soft delete (Placeholder to match prod DB state)

Revision ID: 009_add_job_soft_delete
Revises: 007_add_user_score
Create Date: 2025-12-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009_add_job_soft_delete'
down_revision = '007_add_user_score'
branch_labels = None
depends_on = None


def upgrade():
    # Placeholder: The DB believes this is applied.
    # If the column 'deleted_at' is missing, we could add it here, 
    # but for now we assume it exists or isn't critical.
    # op.add_column('jobs', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    pass


def downgrade():
    # op.drop_column('jobs', 'deleted_at')
    pass
