import datetime
import os
from contextlib import contextmanager

import i18n
import pytest
from sqlalchemy import desc
from sqlalchemy.exc import NoResultFound

from commands.add_food_command import add_food, parse_add_food_message, add_food_parser
from commands.add_unit_command import parse_add_unit_message, add_unit
from commands.food_entry_command import food_entry, parse_food_entry_message
from exc import FoodNotFound
from models import Food, FoodName, FoodLog, date_now, FoodUnit, User, FoodRequest
from models.core import create_food, create_unit, define_unit_for_food, get_food_by_name, get_or_create_user, \
    get_gram_unit, get_unit_by_name


@contextmanager
def do_test_setup(db_session, owner_user, default_units):
    yield


def test_parse_add_unit_message(db_session, owner_user, default_units):
    with do_test_setup(db_session, owner_user, default_units):
        with pytest.raises(ValueError):
            parse_add_unit_message('/invalid')
        with pytest.raises(ValueError):
            parse_add_unit_message('/add_unit')

        data = [
            ('/add_unit Bowl', 'Bowl'),
            ('/add_unit "Small cup"', 'Small cup'),
        ]
        for row in data:
            result = parse_add_unit_message(row[0])
            assert row[1] == result['unit_name']


def test_invalid_user(db_session, owner_user, default_units):
    with do_test_setup(db_session, owner_user, default_units):
        assert db_session.query(User).count() == 1
        user = get_or_create_user(db_session, 12345)
        tid = str(user.telegram_id)
        messages = add_unit(db_session, user, '/add_unit Bowl')
        assert tid in messages
        assert i18n.t('Invalid user id') == messages[tid]


def test_invalid_command(db_session, owner_user, default_units):
    with do_test_setup(db_session, owner_user, default_units):
        assert db_session.query(User).count() == 1
        user = db_session.query(User).one()
        tid = str(user.telegram_id)
        messages = add_unit(db_session, user, '/invalid')
        assert tid in messages
        assert i18n.t('Invalid command format') == messages[tid]

        messages = add_unit(db_session, user, '/add_unit')
        assert tid in messages
        assert i18n.t('Invalid command format') == messages[tid]


def test_duplicate_unit(db_session, owner_user, default_units):
    with do_test_setup(db_session, owner_user, default_units):
        assert db_session.query(User).count() == 1
        user = db_session.query(User).one()
        tid = str(user.telegram_id)
        assert tid == str(os.getenv('OWNER_TELEGRAM_ID'))
        create_unit(db_session, i18n.get('locale'), 'Bowl')
        messages = add_unit(db_session, user, '/add_unit Bowl')
        assert tid in messages
        assert i18n.t('Unit already exists') == messages[tid]


def test_valid(db_session, owner_user, default_units):
    with do_test_setup(db_session, owner_user, default_units):
        assert db_session.query(User).count() == 1
        owner_user = db_session.query(User).one()
        owner_tid = str(owner_user.telegram_id)

        with pytest.raises(NoResultFound):
            get_unit_by_name(db_session=db_session, locale=i18n.get('locale'),
                             name='Bowl')
        messages = add_unit(db_session, owner_user, '/add_unit Bowl')
        assert owner_tid in messages
        assert i18n.t('Unit added') == messages[owner_tid]

        get_unit_by_name(db_session=db_session, locale=i18n.get('locale'),
                         name='Bowl')
