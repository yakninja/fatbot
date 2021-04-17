from contextlib import contextmanager

import pytest
from sqlalchemy.exc import NoResultFound

from exc import FoodNotFound, UnitNotFound, UnitNotDefined
from models import Food, FoodName, FoodLog
from models.core import get_food_by_name, create_food, get_or_create_user, log_food, create_unit, define_unit


@contextmanager
def do_test_setup(db_session, no_food):
    yield


def test_create_food(db_session, no_food):
    with do_test_setup(db_session, no_food):
        assert len(db_session.query(FoodName).all()) == 0
        assert len(db_session.query(Food).all()) == 0
        with pytest.raises(NoResultFound):
            get_food_by_name(db_session, 'en', 'Apple')
        food = create_food(db_session, 'en', 'Apple',
                           calories=0.52, fat=0.002, carbs=0.14, protein=0.003)
        f = get_food_by_name(db_session, 'en', 'Apple')
        assert f.id == food.id
        assert f.calories == 0.52
        assert f.fat == 0.002
        assert f.carbs == 0.14
        assert f.protein == 0.003


def test_log_food(db_session, no_food):
    with do_test_setup(db_session, no_food):
        assert db_session.query(FoodLog).count() == 0
        user = get_or_create_user(db_session, telegram_id='12345')
        with pytest.raises(FoodNotFound):
            log_food(db_session, locale='en', user=user,
                     food_name='Bread', unit_name='slice', qty=2)

        food = create_food(db_session, 'en', 'Bread',
                           calories=2.65, fat=0.032, carbs=0.49, protein=0.09)

        with pytest.raises(UnitNotFound):
            log_food(db_session, locale='en', user=user,
                     food_name='Bread', unit_name='slice', qty=2)

        unit = create_unit(db_session, 'en', 'slice')  # 1 slice = 30 g

        with pytest.raises(UnitNotDefined):
            log_food(db_session, locale='en', user=user,
                     food_name='Bread', unit_name='slice', qty=2)

        define_unit(db_session, food, unit, grams=30, is_default=True)
        log_food(db_session, locale='en', user=user,
                 food_name='Bread', unit_name='slice', qty=2)

        assert db_session.query(FoodLog).count() == 1
