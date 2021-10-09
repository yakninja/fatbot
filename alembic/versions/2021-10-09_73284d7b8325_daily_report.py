"""daily_report

Revision ID: 73284d7b8325
Revises: 863875bf2677
Create Date: 2021-10-09 19:03:59.922742

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '73284d7b8325'
down_revision = '863875bf2677'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'daily_report',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, nullable=False, unique=True),
        sa.Column('last_report_date', sa.Date, nullable=False)
    )
    op.create_index('idx-daily_report-last_report_date', 'daily_report', ['last_report_date'])
    op.create_foreign_key(
        'fk-daily_report-user',
        'daily_report', 'user',
        ['user_id'], ['id'],
        onupdate='restrict',
        ondelete='cascade'
    )


def downgrade():
    op.drop_table('daily_report')
