import datetime
from contextlib import contextmanager

import pytest
from sqlalchemy.exc import NoResultFound

from exc import FoodNotFound, UnitNotFound, UnitNotDefined
from models import Food, FoodName, FoodLog, date_now, FoodUnit
from models.core import get_food_by_name, create_food, get_or_create_user, log_food, create_unit, define_unit_for_food, \
    get_gram_unit


@contextmanager
def do_test_setup(db_session, no_food, default_units):
    yield


def test_create_food(db_session, no_food, default_units):
    with do_test_setup(db_session, no_food, default_units):
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


def test_log_food(db_session, no_food, default_units):
    with do_test_setup(db_session, no_food, default_units):
        assert db_session.query(FoodLog).count() == 0
        user = get_or_create_user(db_session, telegram_id='12345')
        assert user is not None
        with pytest.raises(FoodNotFound):
            log_food(db_session, locale='en', user=user,
                     food_name='Bread', unit_name='slice', qty=2)

        bread_food = create_food(db_session, 'en', 'Bread',
                                 calories=2.65, fat=0.032, carbs=0.49, protein=0.09)

        with pytest.raises(UnitNotFound):
            log_food(db_session, locale='en', user=user,
                     food_name='Bread', unit_name='slice', qty=2)

        slice_unit = create_unit(db_session, 'en', 'slice')  # 1 slice = 30 g

        with pytest.raises(UnitNotDefined):
            log_food(db_session, locale='en', user=user,
                     food_name='Bread', unit_name='slice', qty=2)

        define_unit_for_food(db_session, bread_food, slice_unit, grams=30, is_default=True)
        log_food(db_session, locale='en', user=user,
                 food_name='Bread', unit_name='slice', qty=2)

        food_logs = db_session.query(FoodLog).all()
        assert len(food_logs) == 1
        fl = food_logs[0]
        assert fl.calories == 159.0  # 2.65 per gram, 2 slices = 60 gram, 60 * 2.65 = 159.0
        assert fl.fat == 1.92
        assert fl.carbs == 29.4
        assert fl.protein == 5.4
        assert fl.date.strftime('%Y-%m-%d') == date_now()

        # grams are added implicitly
        log_food(db_session, locale='en', user=user,
                 food_name='Bread', unit_name='g', qty=17,
                 date='2000-01-01')

        food_logs = db_session.query(FoodLog).order_by('id').all()
        assert len(food_logs) == 2
        fl = food_logs[1]
        assert fl.calories == 45.05  # 2.65 per gram, 17 grams, 17 * 2.65 = 45.05
        assert fl.fat == 0.544
        assert fl.carbs == 8.33
        assert fl.protein == 1.53
        assert fl.date.strftime('%Y-%m-%d') == '2000-01-01'

        bread_slice_unit = db_session.query(FoodUnit).filter_by(
            food_id=bread_food.id,
            unit_id=slice_unit.id).one()
        assert bread_slice_unit.grams == 30
        assert bread_slice_unit.is_default

        bread_gram_unit = db_session.query(FoodUnit).filter_by(
            food_id=bread_food.id,
            unit_id=get_gram_unit(db_session).id).one()
        assert bread_gram_unit.grams == 1
        assert not bread_gram_unit.is_default
