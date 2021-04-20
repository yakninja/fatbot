import datetime
from contextlib import contextmanager

import i18n
import pytest
from sqlalchemy.exc import NoResultFound

from commands.food_entry_command import food_entry, parse_food_entry
from models import Food, FoodName, FoodLog, date_now, FoodUnit, User, FoodRequest


@contextmanager
def do_test_setup(db_session, no_users, no_food, default_units):
    yield


def test_parse_food_entry():
    data = [
        ('', None, None, None),
        ('Pineapple', 'Pineapple', 1.0, None),
        ('Apple 1', 'Apple', 1.0, None),
        ('Apple, 9', 'Apple', 9.0, None),
        ('Apple 2.3', 'Apple', 2.3, None),
        ('Apple 3 pc', 'Apple', 3.0, 'pc'),
        ('Apple 4g', 'Apple', 4.0, 'g'),
        ('Apple 4 Oz', 'Apple', 4.0, 'oz'),
        ('Apple 4,5 g', 'Apple', 4.5, 'g'),
        ('Apple, 4,6 g', 'Apple', 4.6, 'g'),
        ('Yoghurt 3%', 'Yoghurt 3%', 1.0, None),
        ('Yoghurt 3% 200', 'Yoghurt 3%', 200.0, None),
        ('Yoghurt 3% 200 g', 'Yoghurt 3%', 200.0, 'g'),
        (' Fresh bread   1  slice ', 'Fresh bread', 1.0, 'slice'),
    ]
    for entry, food_name, unit_name, qty in data:
        assert (food_name, unit_name, qty) == parse_food_entry(entry)


def test_invalid_command(db_session, no_users, no_food, default_units):
    with do_test_setup(db_session, no_users, no_food, default_units):
        assert db_session.query(User).count() == 0
        user_message, owner_message = food_entry(db_session, 12345, '')
        assert user_message == i18n.t('I don\'t understand')


def test_non_existing_food(db_session, no_users, no_food, default_units):
    with do_test_setup(db_session, no_users, no_food, default_units):
        assert db_session.query(User).count() == 0
        assert db_session.query(Food).count() == 0
        assert db_session.query(FoodLog).count() == 0
        assert db_session.query(FoodRequest).count() == 0
        user_reply = i18n.t('The food was not found, forwarding request to the owner')
        owner_reply = i18n.t('Please add new food')
        data = [
            'Apple',
            'Apple 1',
            'Bread 1 slice',
            'Pineapple 100 g',
        ]
        request_count = 0
        for entry in data:
            user_message, owner_message = food_entry(db_session, 12345, entry)
            assert user_message == user_reply
            assert owner_reply in owner_message
            request_count += 1
            assert db_session.query(FoodRequest).count() == request_count

        assert db_session.query(FoodLog).count() == 0
        assert db_session.query(User).count() == 1
