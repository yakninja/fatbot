"""command_log

Revision ID: 14139f2c6c48
Revises: 545e262bdb51
Create Date: 2021-05-05 15:25:07.180186

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '14139f2c6c48'
down_revision = '545e262bdb51'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'command_log',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, nullable=False),
        sa.Column('created_at', sa.Integer, nullable=False),
        sa.Column('command_type', sa.Integer(), nullable=False),
        sa.Column('command', sa.String(255), nullable=False)
    )
    op.create_index('idx-command_log-user_id-created_at', 'command_log', ['user_id', 'created_at'])
    op.create_foreign_key(
        'fk-command_log-user',
        'command_log', 'user',
        ['user_id'], ['id'],
        onupdate='restrict',
        ondelete='cascade'
    )


def downgrade():
    op.drop_table('command_log')
