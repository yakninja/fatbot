"""init

Revision ID: 33b1774e5345
Revises: 
Create Date: 2021-03-21 10:01:47.564249

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '33b1774e5345'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('telegram_id', sa.Integer, nullable=False, unique=True),
        sa.Column('created_at', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.Integer(), nullable=False),
    )
    op.create_table(
        'user_profile',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, nullable=False),
        sa.Column('daily_calories', sa.Float(), nullable=False),
        sa.Column('daily_fat', sa.Float(), nullable=False),
        sa.Column('daily_carbs', sa.Float(), nullable=False),
        sa.Column('daily_protein', sa.Float(), nullable=False),
    )
    op.create_foreign_key(
        'fk-user_profile-user',
        'user_profile', 'user',
        ['user_id'], ['id'],
        onupdate='cascade',
        ondelete='cascade'
    )
    op.create_table(
        'food',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('created_at', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.Integer(), nullable=False),
        sa.Column('calories', sa.Float(), nullable=False),
        sa.Column('fat', sa.Float(), nullable=False),
        sa.Column('carbs', sa.Float(), nullable=False),
        sa.Column('protein', sa.Float(), nullable=False),
    )
    op.create_table(
        'food_name',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('food_id', sa.Integer, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('language', sa.String(8)),
    )
    op.create_foreign_key(
        'fk-food_name-food',
        'food_name', 'food',
        ['food_id'], ['id'],
        onupdate='restrict',
        ondelete='cascade'
    )
    op.create_unique_constraint('uq-food_name', 'food_name', ['food_id', 'name', 'language'])

    op.create_table(
        'food_log',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, nullable=False),
        sa.Column('food_id', sa.Integer, nullable=False),
        sa.Column('created_at', sa.Integer, nullable=False),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('qty', sa.Float(), nullable=False),
        sa.Column('calories', sa.Float(), nullable=False),
        sa.Column('fat', sa.Float(), nullable=False),
        sa.Column('carbs', sa.Float(), nullable=False),
        sa.Column('protein', sa.Float(), nullable=False),
    )
    op.create_foreign_key(
        'fk-food_log-food',
        'food_log', 'food',
        ['food_id'], ['id'],
        onupdate='restrict',
        ondelete='cascade'
    )
    op.create_foreign_key(
        'fk-food_log-user',
        'food_log', 'user',
        ['user_id'], ['id'],
        onupdate='restrict',
        ondelete='cascade'
    )
    op.create_index('idx-food_log-user_id-date-created_at', 'food_log', ['user_id', 'date', 'created_at'])

    op.create_table(
        'food_request',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, nullable=False),
        sa.Column('created_at', sa.Integer, nullable=False),
        sa.Column('qty', sa.Float(), nullable=False),
        sa.Column('request', sa.String(255), nullable=False),
    )


def downgrade():
    op.drop_table('food_request')
    op.drop_table('food_log')
    op.drop_table('food_name')
    op.drop_table('food')
    op.drop_table('user_profile')
    op.drop_table('user')
