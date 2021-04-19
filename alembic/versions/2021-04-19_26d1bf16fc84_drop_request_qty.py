"""drop_request_qty

Revision ID: 26d1bf16fc84
Revises: 66620fa9c5fa
Create Date: 2021-04-19 19:05:08.457310

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '26d1bf16fc84'
down_revision = '66620fa9c5fa'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('food_request', 'qty')


def downgrade():
    op.add_column('food_request', sa.Column('qty', sa.Float(), nullable=False))
