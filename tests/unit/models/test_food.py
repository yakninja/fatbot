from contextlib import contextmanager

import pytest
from sqlalchemy.exc import NoResultFound

from models import Food, FoodName
from models.core import get_food_by_name, create_food


@contextmanager
def do_test_setup(db_session, no_food):
    yield


def test_create_food(db_session, no_food):
    with do_test_setup(db_session, no_food):
        assert len(db_session.query(FoodName).all()) == 0
        assert len(db_session.query(Food).all()) == 0
        with pytest.raises(NoResultFound):
            get_food_by_name(db_session, 'en', 'Apple')
        create_food(db_session, 'en', 'Apple',
                    calories=10, fat=11, carbs=12, protein=13)
        f = get_food_by_name(db_session, 'en', 'Apple')
        assert f.calories == 10
        assert f.fat == 11
        assert f.carbs == 12
        assert f.protein == 13
