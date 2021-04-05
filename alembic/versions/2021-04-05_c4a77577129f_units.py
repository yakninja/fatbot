"""units

Revision ID: c4a77577129f
Revises: 33b1774e5345
Create Date: 2021-04-05 10:57:17.396112

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy import func

revision = 'c4a77577129f'
down_revision = '33b1774e5345'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('food', sa.Column('default_unit', sa.String(16), nullable=False,
                  server_default='g'))
    op.add_column('food', sa.Column('g_per_unit', sa.Float(), nullable=False,
                  server_default='1.0'))


def downgrade():
    op.drop_column('food', 'g_per_unit')
    op.drop_column('food', 'default_unit')
