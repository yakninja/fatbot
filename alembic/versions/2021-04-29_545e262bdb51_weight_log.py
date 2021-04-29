"""weight_log

Revision ID: 545e262bdb51
Revises: 6611998d6983
Create Date: 2021-04-29 14:45:35.154564

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '545e262bdb51'
down_revision = '6611998d6983'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'weight_log',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, nullable=False),
        sa.Column('created_at', sa.Integer, nullable=False),
        sa.Column('weight', sa.Float(), nullable=False),
    )
    op.create_index('idx-weight_log-user_id-created_at', 'food_log', ['user_id', 'created_at'])
    op.create_foreign_key(
        'fk-weight_log-user',
        'weight_log', 'user',
        ['user_id'], ['id'],
        onupdate='restrict',
        ondelete='cascade'
    )


def downgrade():
    op.drop_table('weight_log')
