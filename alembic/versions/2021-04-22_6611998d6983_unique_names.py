"""unique_names

Revision ID: 6611998d6983
Revises: 26d1bf16fc84
Create Date: 2021-04-22 16:32:41.949480

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
from sqlalchemy import orm, text

revision = '6611998d6983'
down_revision = '26d1bf16fc84'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('fk-food_name-food', 'food_name', type_='foreignkey')
    op.drop_constraint('fk-unit_name-unit', 'unit_name', type_='foreignkey')
    op.drop_constraint('uq-food_name', 'food_name', type_='unique')
    op.drop_constraint('uq-unit_name', 'unit_name', type_='unique')

    session = orm.Session(bind=op.get_bind())

    # otherwise we risk getting "You can't specify target table for update in FROM clause"
    session.execute(text("SET optimizer_switch = 'derived_merge=off'"))

    # delete duplicate names
    session.execute(text("""DELETE FROM food_name fn
    WHERE fn.id NOT IN(SELECT * FROM(SELECT max(id) FROM food_name fn2
        WHERE fn2.name = fn.name AND fn2.language = fn2.language) x)"""))
    session.execute(text("""DELETE FROM unit_name un
    WHERE un.id NOT IN(SELECT * FROM(SELECT max(id) FROM unit_name un2
        WHERE un2.name = un.name AND un2.language = un2.language) x)"""))
    session.commit()

    op.create_unique_constraint('uq-food_name-name-language', 'food_name',
                                ['name', 'language'])
    op.create_unique_constraint('uq-unit_name-name-language', 'unit_name',
                                ['name', 'language'])

    op.create_foreign_key(
        'fk-food_name-food',
        'food_name', 'food',
        ['food_id'], ['id'],
        onupdate='restrict',
        ondelete='cascade'
    )

    op.create_foreign_key(
        'fk-unit_name-unit',
        'unit_name', 'unit',
        ['unit_id'], ['id'],
        onupdate='restrict',
        ondelete='cascade'
    )


def downgrade():
    op.drop_constraint('fk-food_name-food', 'food_name', type_='foreignkey')
    op.drop_constraint('fk-unit_name-unit', 'unit_name', type_='foreignkey')
    op.drop_constraint('uq-food_name-name-language', 'food_name', type_='unique')
    op.drop_constraint('uq-unit_name-name-language', 'unit_name', type_='unique')
    op.create_unique_constraint('uq-unit_name', 'unit_name',
                                ['unit_id', 'name', 'language'])
    op.create_unique_constraint('uq-food_name', 'food_name',
                                ['food_id', 'name', 'language'])

    op.create_foreign_key(
        'fk-food_name-food',
        'food_name', 'food',
        ['food_id'], ['id'],
        onupdate='restrict',
        ondelete='cascade'
    )

    op.create_foreign_key(
        'fk-unit_name-unit',
        'unit_name', 'unit',
        ['unit_id'], ['id'],
        onupdate='restrict',
        ondelete='cascade'
    )
