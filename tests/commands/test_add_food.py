import datetime
from contextlib import contextmanager

import i18n
import pytest
from sqlalchemy import desc
from sqlalchemy.exc import NoResultFound

from commands.add_food_command import add_food
from commands.food_entry_command import food_entry, parse_food_entry_message
from models import Food, FoodName, FoodLog, date_now, FoodUnit, User, FoodRequest
from models.core import create_food, create_unit, define_unit_for_food, get_food_by_name, get_or_create_user, \
    get_gram_unit


@contextmanager
def do_test_setup(db_session, owner_user, no_food, default_units):
    yield


def test_parse_command(db_session, no_food, default_units):
    with do_test_setup(db_session, no_food, default_units):
        data = [
        ]


def test_invalid_user(db_session, owner_user, no_food, default_units):
    with do_test_setup(db_session, owner_user, no_food, default_units):
        assert db_session.query(User).count() == 1
        user = get_or_create_user(db_session, 12345)
        user_message, owner_message = add_food(
            db_session, user, '/add_food "Chicken soup" calories:36 fat:1.2 carbs:3.5 protein:2.5')
        assert i18n.t('Invalid user id') == user_message


def test_invalid_command(db_session, owner_user, no_food, default_units):
    with do_test_setup(db_session, owner_user, no_food, default_units):
        assert db_session.query(User).count() == 1
        user = db_session.query(User).one()
        user_message, owner_message = add_food(
            db_session, user, '/invalid "Chicken soup" calories:36 fat:1.2 carbs:3.5 protein:2.5')
        assert i18n.t('Invalid command format') == user_message
