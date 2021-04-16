"""remove_food_fields

Revision ID: 66620fa9c5fa
Revises: d6b9271522d9
Create Date: 2021-04-16 12:06:52.007534

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '66620fa9c5fa'
down_revision = 'd6b9271522d9'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('food', 'default_unit')
    op.drop_column('food', 'g_per_unit')


def downgrade():
    op.add_column(
        'food',
        sa.Column('default_unit', sa.String(255), nullable=False,
                  server_default='g')
    )
    op.add_column(
        'food',
        sa.Column('g_per_unit', sa.Float, nullable=False,
                  server_default='1')
    )
