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
from commands.weight_entry_command import weight_entry
from exc import FoodNotFound
from models import Food, FoodName, FoodLog, date_now, FoodUnit, User, FoodRequest, WeightLog
from models.core import create_food, create_unit, define_unit_for_food, get_food_by_name, get_or_create_user, \
    get_gram_unit, get_unit_by_name


@contextmanager
def do_test_setup(db_session, no_users):
    yield


def test_invalid_command(db_session, no_users):
    with do_test_setup(db_session, no_users):
        assert db_session.query(User).count() == 0
        user = get_or_create_user(db_session, 12345)
        tid = str(user.telegram_id)
        invalid = [
            '',
            '/invalid',
            '/weight'
            '/weight 0',
            '/weight 0.0',
        ]
        for entry in invalid:
            messages = weight_entry(db_session, user, entry)
            assert tid in messages
            assert messages[tid] == i18n.t('I don\'t understand')


def test_valid_command(db_session, no_users):
    with do_test_setup(db_session, no_users):
        assert db_session.query(WeightLog).count() == 0
        user = get_or_create_user(db_session, 12345)
        tid = str(user.telegram_id)
        owner_id = os.getenv('OWNER_TELEGRAM_ID')
        messages = weight_entry(db_session, user, '/weight 50')
        assert tid in messages
        assert owner_id in messages
        assert messages[tid] == i18n.t('Weight recorded: %{weight}', weight='50.0')
        assert messages[owner_id] == i18n.t('Weight recorded: %{weight}', weight='50.0')
        assert db_session.query(WeightLog).count() == 1
        weight_log = db_session.query(WeightLog).order_by(desc('id')).first()
        assert weight_log.user_id == user.id
        assert weight_log.weight == 50

        messages = weight_entry(db_session, user, '/weight 50.5')
        assert tid in messages
        assert owner_id in messages
        assert messages[tid] == i18n.t('Weight recorded: %{weight}', weight='50.5')
        assert messages[owner_id] == i18n.t('Weight recorded: %{weight}', weight='50.5')
        assert db_session.query(WeightLog).count() == 2
        weight_log = db_session.query(WeightLog).order_by(desc('id')).first()
        assert weight_log.user_id == user.id
        assert weight_log.weight == 50.5
