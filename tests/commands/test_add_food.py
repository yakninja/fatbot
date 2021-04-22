import datetime
from contextlib import contextmanager

import i18n
import pytest
from sqlalchemy import desc
from sqlalchemy.exc import NoResultFound

from commands.food_entry_command import food_entry, parse_food_entry
from models import Food, FoodName, FoodLog, date_now, FoodUnit, User, FoodRequest
from models.core import create_food, create_unit, define_unit_for_food, get_food_by_name, get_or_create_user, \
    get_gram_unit


@contextmanager
def do_test_setup(db_session, owner_user, no_food, default_units):
    yield


def test_invalid_user(db_session, owner_user, no_food, default_units):
    with do_test_setup(db_session, owner_user, no_food, default_units):
        assert db_session.query(User).count() == 1
