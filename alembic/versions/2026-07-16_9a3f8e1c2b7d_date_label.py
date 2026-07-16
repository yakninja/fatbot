"""date_label

Revision ID: 9a3f8e1c2b7d
Revises: 73284d7b8325
Create Date: 2026-07-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a3f8e1c2b7d'
down_revision = '73284d7b8325'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'date_label',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, nullable=False),
        sa.Column('created_at', sa.Integer, nullable=False),
        sa.Column('updated_at', sa.Integer, nullable=False),
        sa.Column('label_date', sa.Date, nullable=False),
        sa.Column('label', sa.String(32), nullable=False),
    )
    op.create_index(
        'idx-date_label-user_id-label_date',
        'date_label',
        ['user_id', 'label_date'],
        unique=True,
    )
    op.create_foreign_key(
        'fk-date_label-user',
        'date_label', 'user',
        ['user_id'], ['id'],
        onupdate='restrict',
        ondelete='cascade',
    )


def downgrade():
    op.drop_table('date_label')
