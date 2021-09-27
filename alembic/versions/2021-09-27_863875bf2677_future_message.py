"""future_message

Revision ID: 863875bf2677
Revises: 14139f2c6c48
Create Date: 2021-09-27 16:03:30.329480

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '863875bf2677'
down_revision = '14139f2c6c48'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'future_message',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('send_at', sa.DateTime, nullable=False),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('locked_until', sa.DateTime, nullable=False),
        sa.Column('message', sa.String(1024), nullable=False)
    )
    op.create_index('idx-future_message-user_id', 'future_message', ['user_id'])
    op.create_index('idx-future_message-send_at-created_at', 'future_message', ['send_at', 'created_at'])
    op.create_index('idx-future_message-expires_at', 'future_message', ['expires_at'])
    op.create_foreign_key(
        'fk-future_message-user',
        'future_message', 'user',
        ['user_id'], ['id'],
        onupdate='restrict',
        ondelete='cascade'
    )


def downgrade():
    op.drop_table('future_message')
