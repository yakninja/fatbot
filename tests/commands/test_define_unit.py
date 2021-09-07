import datetime
import os
from contextlib import contextmanager

import i18n
import pytest
from sqlalchemy import desc
from sqlalchemy.exc import NoResultFound

from commands.add_food_command import add_food, parse_add_food_message, add_food_parser
from commands.define_unit_command import parse_define_unit_message, define_unit
from commands.food_entry_command import food_entry, parse_food_entry_message
from exc import FoodNotFound
from models import Food, FoodName, FoodLog, date_now, FoodUnit, User, FoodRequest
from models.core import create_food, create_unit, define_unit_for_food, get_food_by_name, get_or_create_user, \
    get_gram_unit, get_unit_by_name


@contextmanager
def do_test_setup(db_session, owner_user, no_food, default_units):
    yield


def test_parse_define_unit_message(db_session, owner_user, no_food, default_units):
    with do_test_setup(db_session, owner_user, no_food, default_units):
        data = [
            (
                '/define_unit "Chicken soup" Bowl --grams=350',
                {
                    'food_name': 'Chicken soup', 'unit_name': 'Bowl', 'grams': 350.0,
                    'default': False, 'request': None,
                }
            ),
            (
                '/define_unit Borscht "Small bowl" --grams=222.5 --default=True --request=123',
                {
                    'food_name': 'Borscht', 'unit_name': 'Small bowl', 'grams': 222.5,
                    'default': True, 'request': 123,
                }
            ),
            ('/define_unit A B --grams=0 --default=Y', {'default': True}),
            ('/define_unit A B --grams=0 --default=yes', {'default': True}),
            ('/define_unit A B --grams=0 --default=1', {'default': True}),
            ('/define_unit A B --grams=0 --default=false', {'default': False}),
            ('/define_unit A B --grams=0 --default=No', {'default': False}),
            ('/define_unit A B --grams=0 --default=n', {'default': False}),
            ('/define_unit A B --grams=0 --default=0', {'default': False}),
        ]
        with pytest.raises(ValueError):
            parse_define_unit_message('/invalid')
        with pytest.raises(ValueError):
            parse_define_unit_message('/define_unit "Chicken soup"')
        for row in data:
            result = parse_define_unit_message(row[0])
            for k in row[1].keys():
                assert result[k] == row[1][k]


def test_invalid_user(db_session, owner_user, no_food, default_units):
    with do_test_setup(db_session, owner_user, no_food, default_units):
        assert db_session.query(User).count() == 1
        user = get_or_create_user(db_session, 12345)
        assert user is not None
        tid = str(user.telegram_id)
        messages = define_unit(db_session, user, '/define_unit "Chicken soup" Bowl --grams=350')
        assert tid in messages
        assert i18n.t('Invalid user id') == messages[tid]


def test_invalid_command(db_session, owner_user, no_food, default_units):
    with do_test_setup(db_session, owner_user, no_food, default_units):
        assert db_session.query(User).count() == 1
        user = db_session.query(User).one()
        tid = str(user.telegram_id)
        messages = define_unit(db_session, user, '/invalid')
        assert tid in messages
        assert i18n.t('Invalid command format') == messages[tid]

        messages = define_unit(db_session, user, '/define_unit')
        assert tid in messages
        assert i18n.t('Invalid command format') == messages[tid]

        messages = define_unit(db_session, user, '/define_unit "Chicken soup"')
        assert tid in messages
        assert i18n.t('Invalid command format') == messages[tid]

        messages = define_unit(db_session, user, '/define_unit "Chicken soup" Bowl')
        assert tid in messages
        assert i18n.t('Invalid command format') == messages[tid]


def test_valid(db_session, owner_user, no_food, default_units):
    with do_test_setup(db_session, owner_user, no_food, default_units):
        assert db_session.query(User).count() == 1
        assert db_session.query(FoodLog).count() == 0
        assert db_session.query(FoodRequest).count() == 0
        owner_user = db_session.query(User).one()
        owner_tid = str(owner_user.telegram_id)

        with pytest.raises(NoResultFound):
            get_food_by_name(db_session=db_session, locale=i18n.get('locale'),
                             food_name='Chicken soup')
        with pytest.raises(NoResultFound):
            get_unit_by_name(db_session=db_session, locale=i18n.get('locale'),
                             unit_name='Bowl')

        messages = define_unit(db_session, owner_user, '/define_unit "Chicken soup" Bowl --grams=350')
        assert owner_tid in messages
        assert i18n.t('Food does not exist') in messages[owner_tid]

        food = create_food(db_session=db_session, locale=i18n.get('locale'),
                           food_name='Chicken soup', calories=36, fat=1.2, carbs=3.5, protein=2.5)

        messages = define_unit(db_session, owner_user, '/define_unit "Chicken soup" Bowl --grams=350')
        assert owner_tid in messages
        assert i18n.t('Unit does not exist') in messages[owner_tid]

        unit = create_unit(db_session=db_session, locale=i18n.get('locale'),
                           unit_name='Bowl')

        messages = define_unit(db_session, owner_user, '/define_unit "Chicken soup" Bowl --grams=350')
        assert owner_tid in messages
        assert i18n.t('Unit defined') in messages[owner_tid]


def test_valid_with_request(db_session, owner_user, no_food, default_units):
    with do_test_setup(db_session, owner_user, no_food, default_units):
        owner_user = db_session.query(User).one()
        owner_tid = str(owner_user.telegram_id)
        user = get_or_create_user(db_session, 12345)
        assert user is not None
        tid = str(user.telegram_id)

        food = create_food(db_session=db_session, locale=i18n.get('locale'),
                           food_name='Chicken soup', calories=0.36, fat=0.012, carbs=0.035, protein=0.025)
        unit = create_unit(db_session=db_session, locale=i18n.get('locale'),
                           unit_name='Bowl')

        food_entry(db_session, user, 'Chicken soup 2 Bowl')
        assert db_session.query(FoodRequest).count() == 1
        assert db_session.query(FoodLog).count() == 0
        request = db_session.query(FoodRequest).first()
        assert request.request == 'Chicken soup 2 Bowl'

        messages = define_unit(
            db_session, owner_user,
            '/define_unit "Chicken soup" Bowl --grams=350 --request={}'.format(request.id)
        )
        assert owner_tid in messages
        assert i18n.t('Unit defined') in messages[owner_tid]
        assert tid in messages
        assert i18n.t('Food added') in messages[tid]
        assert db_session.query(FoodLog).count() == 1
        food_log = db_session.query(FoodLog).first()
        assert food_log.calories == 252  # 36 * 2 * 3.5
        assert food_log.fat == 8.4
        assert food_log.carbs == 24.5
        assert food_log.protein == 17.5
