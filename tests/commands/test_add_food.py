import datetime
import os
from contextlib import contextmanager

import i18n
import pytest
from sqlalchemy import desc
from sqlalchemy.exc import NoResultFound

from commands.add_food_command import add_food, parse_add_food_message, add_food_parser
from commands.food_entry_command import food_entry, parse_food_entry_message
from exc import FoodNotFound
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
        tid = str(user.telegram_id)
        messages = add_food(
            db_session,
            user,
            '/add_food "Chicken soup" --calories=36 --fat=1.2 --carbs=3.5 --protein=2.5'
        )
        assert tid in messages
        assert i18n.t('Invalid user id') == messages[tid]


def test_invalid_command(db_session, owner_user, no_food, default_units):
    with do_test_setup(db_session, owner_user, no_food, default_units):
        assert db_session.query(User).count() == 1
        user = db_session.query(User).one()
        tid = str(user.telegram_id)
        messages = add_food(
            db_session,
            user,
            '/invalid "Chicken soup" --calories=36 --fat=1.2 --carbs=3.5 --protein=2.5'
        )
        assert tid in messages
        assert i18n.t('Invalid command format') == messages[tid]

        messages = add_food(
            db_session,
            user,
            '/add_food "Chicken soup"'  # calories required
        )
        assert tid in messages
        assert i18n.t('Invalid command format') == messages[tid]


def test_duplicate_food(db_session, owner_user, no_food, default_units):
    with do_test_setup(db_session, owner_user, no_food, default_units):
        assert db_session.query(User).count() == 1
        user = db_session.query(User).one()
        tid = str(user.telegram_id)
        assert tid == str(os.getenv('OWNER_TELEGRAM_ID'))
        create_food(db_session, i18n.get('locale'), 'Chicken soup', 0.36)
        messages = add_food(
            db_session,
            user,
            '/add_food "Chicken soup" --calories=36 --fat=1.2 --carbs=3.5 --protein=2.5'
        )
        assert tid in messages
        assert i18n.t('Food already exists') == messages[tid]


def test_valid(db_session, owner_user, no_food, default_units):
    """
    Just add food with name/values, no prior food request
    :param db_session:
    :param owner_user:
    :param no_food:
    :param default_units:
    :return:
    """
    with do_test_setup(db_session, owner_user, no_food, default_units):
        assert db_session.query(User).count() == 1
        assert db_session.query(FoodLog).count() == 0
        assert db_session.query(FoodRequest).count() == 0
        owner_user = db_session.query(User).one()
        owner_tid = str(owner_user.telegram_id)

        with pytest.raises(NoResultFound):
            get_food_by_name(db_session=db_session, locale=i18n.get('locale'),
                             food_name='Chicken soup')

        messages = add_food(
            db_session,
            owner_user,
            '/add_food "Chicken soup" --calories=36 --fat=1.2 --carbs=3.5 --protein=2.5'
        )
        assert owner_tid in messages
        assert i18n.t('Food added') == messages[owner_tid]

        food = get_food_by_name(db_session=db_session, locale=i18n.get('locale'),
                                food_name='Chicken soup')
        assert food.calories == 0.36
        assert food.fat == 0.012
        assert food.carbs == 0.035
        assert food.protein == 0.025
        assert db_session.query(FoodLog).count() == 0

        gram_unit = get_gram_unit(db_session)
        food_unit = db_session.query(FoodUnit).filter_by(
            food_id=food.id, unit_id=gram_unit.id).one()
        assert food_unit.grams == 1
        assert food_unit.is_default


def test_valid_request_grams(db_session, owner_user, no_food, default_units):
    """
    Add food with implicitly defined unit (g) and prior food request, i.e:

    user: Apple 120 g
    ... food request record created
    owner: /add_food Apple --calories=... --request=...
    ... food request gets resolved
    ... user gets a reply with log entry

    :param db_session:
    :param owner_user:
    :param no_food:
    :param default_units:
    :return:
    """
    with do_test_setup(db_session, owner_user, no_food, default_units):
        assert db_session.query(User).count() == 1
        assert db_session.query(FoodRequest).count() == 0
        assert db_session.query(FoodLog).count() == 0
        owner_user = db_session.query(User).one()
        owner_tid = str(owner_user.telegram_id)
        user = get_or_create_user(db_session, 12345)
        tid = str(user.telegram_id)

        with pytest.raises(NoResultFound):
            get_food_by_name(db_session=db_session, locale=i18n.get('locale'),
                             food_name='Apple')

        food_entry(db_session, user, 'Apple 120 g')
        assert db_session.query(FoodRequest).count() == 1
        assert db_session.query(FoodLog).count() == 0
        request = db_session.query(FoodRequest).first()
        assert request.request == 'Apple 120 g'

        messages = add_food(
            db_session, owner_user,
            '/add_food Apple --calories=52 --fat=0.2 ' +
            '--carbs=14 --protein=0.3 --request={}'.format(request.id))
        assert owner_tid in messages
        assert tid in messages
        assert i18n.t('Food added') in messages[owner_tid]
        assert i18n.t('Food added') in messages[tid]
        assert db_session.query(FoodLog).count() == 1
        food_log = db_session.query(FoodLog).first()
        assert food_log.calories == 62.4  # 52 * 1.2
        assert food_log.fat == 0.24
        assert food_log.carbs == 16.8
        assert food_log.protein == 0.36
