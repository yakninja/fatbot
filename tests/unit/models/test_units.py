from contextlib import contextmanager

import pytest
from sqlalchemy.exc import NoResultFound

from models import Food, FoodName, FoodUnit
from models.core import get_food_by_name, create_food, get_unit_by_name, create_unit, define_unit_for_food, \
    get_gram_unit


@contextmanager
def do_test_setup(db_session, no_food, default_units):
    yield


def test_create_unit(db_session, no_food, default_units):
    with do_test_setup(db_session, no_food, default_units):
        with pytest.raises(NoResultFound):
            get_unit_by_name(db_session, 'en', 'Bowl')
        create_unit(db_session, 'en', 'Bowl')
        get_unit_by_name(db_session, 'en', 'Bowl')


def test_define_unit(db_session, no_food, default_units):
    with do_test_setup(db_session, no_food, default_units):
        food = create_food(db_session, 'en', 'Soup')
        unit = create_unit(db_session, 'en', 'Bowl')
        gram_food_unit = db_session.query(FoodUnit).filter_by(
            food_id=food.id, unit_id=get_gram_unit(db_session).id).one()
        assert gram_food_unit.grams == 1
        assert gram_food_unit.is_default

        define_unit_for_food(db_session, food, unit, 350, True)
        food_unit = db_session.query(FoodUnit).filter_by(food_id=food.id, unit_id=unit.id).one()
        assert food_unit.grams == 350
        assert food_unit.is_default
