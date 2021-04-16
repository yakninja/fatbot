from contextlib import contextmanager

import pytest
from sqlalchemy.exc import NoResultFound

from models import Food, FoodName
from models.core import get_food_by_name, create_food


@contextmanager
def do_test_setup(db_session):
    yield


def test_create_unit(db_session):
    with do_test_setup(db_session):
        pass
