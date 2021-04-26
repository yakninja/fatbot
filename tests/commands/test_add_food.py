import datetime
import os
from contextlib import contextmanager

import i18n
import pytest
from sqlalchemy import desc
from sqlalchemy.exc import NoResultFound

from commands.add_food_command import add_food, parse_add_food_message, add_food_parser
from commands.food_entry_command import food_entry, parse_food_entry_message
from models import Food, FoodName, FoodLog, date_now, FoodUnit, User, FoodRequest
from models.core import create_food, create_unit, define_unit_for_food, get_food_by_name, get_or_create_user, \
    get_gram_unit


@contextmanager
def do_test_setup(db_session, owner_user, no_food, default_units):
    yield


def test_parse_add_food_message(db_session, owner_user, no_food, default_units):
    with do_test_setup(db_session, owner_user, no_food, default_units):
        data = [
            (
                '/add_food "Chicken soup" --calories=36 --fat=1.2 --carbs=3.5 --protein=2.5',
                {
                    'food_name': 'Chicken soup', 'calories': 36.0, 'fat': 1.2,
                    'carbs': 3.5, 'protein': 2.5, 'request': None,
                }
            ),
            (
                '/add_food "Chicken soup" --calories=36.0',
                {
                    'food_name': 'Chicken soup', 'calories': 36.0, 'fat': 0,
                    'carbs': 0, 'protein': 0, 'request': None,
                }
            ),
            (
                '/add_food Apple --p=.01 --calories=8 --req=123',
                {
                    'food_name': 'Apple', 'calories': 8, 'fat': 0,
                    'carbs': 0, 'protein': 0.01, 'request': 123,
                }
            ),
        ]
        with pytest.raises(ValueError):
            parse_add_food_message('/invalid')
        with pytest.raises(ValueError):
            parse_add_food_message('/add_food "Chicken soup"')
        for row in data:
            result = parse_add_food_message(row[0])
            for k in row[1].keys():
                assert result[k] == row[1][k]


def test_invalid_user(db_session, owner_user, no_food, default_units):
    with do_test_setup(db_session, owner_user, no_food, default_units):
        assert db_session.query(User).count() == 1
        user = get_or_create_user(db_session, 12345)
        user_message, owner_message = add_food(
            db_session, user, '/add_food "Chicken soup" --calories=36 --fat=1.2 --carbs=3.5 --protein=2.5')
        assert i18n.t('Invalid user id') == user_message


def test_invalid_command(db_session, owner_user, no_food, default_units):
    with do_test_setup(db_session, owner_user, no_food, default_units):
        assert db_session.query(User).count() == 1
        user = db_session.query(User).one()
        user_message, owner_message = add_food(
            db_session, user, '/invalid "Chicken soup" --calories=36 --fat=1.2 --carbs=3.5 --protein=2.5')
        assert i18n.t('Invalid command format') == user_message


def test_duplicate_food(db_session, owner_user, no_food, default_units):
    with do_test_setup(db_session, owner_user, no_food, default_units):
        assert db_session.query(User).count() == 1
        user = db_session.query(User).one()
        assert str(user.telegram_id) == str(os.getenv('OWNER_USER_ID'))
        create_food(db_session, i18n.get('locale'), 'Chicken soup', 0.36)
        user_message, owner_message = add_food(
            db_session, user, '/add_food "Chicken soup" --calories=36 --fat=1.2 --carbs=3.5 --protein=2.5')
        assert i18n.t('Food already exists') == user_message


def test_valid(db_session, owner_user, no_food, default_units):
    with do_test_setup(db_session, owner_user, no_food, default_units):
        assert db_session.query(User).count() == 1
        user = db_session.query(User).one()
        user_message, owner_message = add_food(
            db_session, user, '/add_food "Chicken soup" --calories=36 --fat=1.2 --carbs=3.5 --protein=2.5')
        assert i18n.t('Food added') == user_message
