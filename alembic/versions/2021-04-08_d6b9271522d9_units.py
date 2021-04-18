"""units

Revision ID: d6b9271522d9
Revises: c4a77577129f
Create Date: 2021-04-08 15:53:37.106825

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.sql import insert, text
from sqlalchemy import orm, String, Integer, Boolean, Float

# revision identifiers, used by Alembic.
from sqlalchemy import table, column

from models.core import create_default_units

revision = 'd6b9271522d9'
down_revision = 'c4a77577129f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'unit',
        sa.Column('id', sa.Integer, primary_key=True)
    )
    op.create_table(
        'unit_name',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('unit_id', sa.Integer, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('language', sa.String(8)),
    )
    op.create_foreign_key(
        'fk-unit_name-unit',
        'unit_name', 'unit',
        ['unit_id'], ['id'],
        onupdate='restrict',
        ondelete='cascade'
    )
    op.create_unique_constraint('uq-unit_name', 'unit_name',
                                ['unit_id', 'name', 'language'])

    op.create_table(
        'food_unit',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('food_id', sa.Integer, nullable=False),
        sa.Column('unit_id', sa.Integer, nullable=False),
        sa.Column('is_default', sa.Boolean, nullable=False),
        sa.Column('grams', sa.Float, nullable=False, server_default='1.0')
    )
    op.create_foreign_key(
        'fk-food_unit-food',
        'food_unit', 'food',
        ['food_id'], ['id'],
        onupdate='restrict',
        ondelete='cascade'
    )
    op.create_foreign_key(
        'fk-food_unit-unit',
        'food_unit', 'unit',
        ['unit_id'], ['id'],
        onupdate='restrict',
        ondelete='cascade'
    )
    op.create_unique_constraint('uq-food_unit', 'food_unit',
                                ['food_id', 'unit_id'])

    op.add_column(
        'food_log',
        sa.Column('unit_id', sa.Integer, nullable=False)
    )

    food_unit = table(
        'food_unit',
        column('food_id', Integer),
        column('unit_id', Integer),
        column('is_default', Boolean),
        column('grams', Float)
    )
    session = orm.Session(bind=op.get_bind())
    gram_unit_id, pc_unit_id = create_default_units(session=session)

    for f in session.execute('SELECT * FROM food'):
        session.execute(
            insert(food_unit).values(
                {
                    'food_id': f['id'],
                    'unit_id': gram_unit_id,
                    'is_default': f['default_unit'] == 'g',
                    'grams': 1
                }
            )
        )
        if f['default_unit'] != 'g':
            session.execute(
                insert(food_unit).values(
                    {
                        'food_id': f['id'],
                        'unit_id': pc_unit_id,
                        'is_default': True,
                        'grams': f['g_per_unit']
                    }
                )
            )
        session.execute("""UPDATE food_log SET unit_id = :unit_id
            WHERE food_id = :food_id""",
                        {
                            'unit_id': gram_unit_id
                            if f['default_unit'] == 'g'
                            else pc_unit_id,
                            'food_id': f['id'],
                        })

    session.execute(text("""UPDATE food SET calories = calories / 100,
        fat = fat / 100,
        carbs = carbs / 100,
        protein = protein / 100"""))

    op.create_foreign_key(
        'fk-food_log-unit',
        'food_log', 'unit',
        ['unit_id'], ['id'],
        onupdate='restrict',
        ondelete='restrict'
    )


def downgrade():
    session = orm.Session(bind=op.get_bind())
    session.execute(text("""UPDATE food SET calories = calories * 100,
        fat = fat * 100,
        carbs = carbs * 100,
        protein = protein * 100"""))
    op.drop_constraint('fk-food_log-unit', 'food_log', type_='foreignkey')
    op.drop_column('food_log', 'unit_id')
    op.drop_table('food_unit')
    op.drop_table('unit_name')
    op.drop_table('unit')
