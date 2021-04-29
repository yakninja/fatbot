import os
from contextlib import contextmanager

import i18n
from sqlalchemy import desc

from commands.food_entry_command import food_entry, parse_food_entry_message
from models import FoodLog, date_now, User, FoodRequest
from models.core import create_food, create_unit, define_unit_for_food, get_or_create_user, \
    get_gram_unit


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
        assert (food_name, unit_name, qty) == parse_food_entry_message(entry)


def test_invalid_command(db_session, no_users, no_food, default_units):
    with do_test_setup(db_session, no_users, no_food, default_units):
        assert db_session.query(User).count() == 0
        user = get_or_create_user(db_session, 12345)
        messages = food_entry(db_session, user, '')
        tid = str(user.telegram_id)
        assert tid in messages
        assert messages[tid] == i18n.t('I don\'t understand')


def test_non_existing_food(db_session, no_users, no_food, default_units):
    with do_test_setup(db_session, no_users, no_food, default_units):
        user_reply = i18n.t('The food was not found, forwarding request to the owner')
        owner_reply = i18n.t('Please add new food (values per 100 g)')
        data = [
            'Apple',
            'Apple 1',
            'Bread 1 slice',
            'Pineapple 100 g',
        ]
        request_count = 0
        user = get_or_create_user(db_session, 12345)
        tid = str(user.telegram_id)
        owner_id = os.getenv('OWNER_TELEGRAM_ID')
        for entry in data:
            messages = food_entry(db_session, user, entry)
            assert tid in messages
            assert owner_id in messages
            assert messages[tid] == user_reply
            assert owner_reply in messages[owner_id]
            request_count += 1
            assert db_session.query(FoodRequest).count() == request_count

        assert db_session.query(FoodLog).count() == 0
        assert db_session.query(User).count() == 1


def test_non_existing_unit(db_session, no_users, no_food, default_units):
    with do_test_setup(db_session, no_users, no_food, default_units):
        user_reply = i18n.t('The food was not found, forwarding request to the owner')
        owner_reply = i18n.t('Please add and define new unit')
        create_food(db_session, i18n.get('locale'), 'Chicken soup',
                    0.36, 0.012, 0.035, 0.025)
        user = get_or_create_user(db_session, 12345)
        tid = str(user.telegram_id)
        owner_id = os.getenv('OWNER_TELEGRAM_ID')
        messages = food_entry(db_session, user,
                              'Chicken soup 1 bowl')
        assert tid in messages
        assert owner_id in messages
        assert messages[tid] == user_reply
        assert owner_reply in messages[owner_id]
        assert db_session.query(FoodLog).count() == 0
        assert db_session.query(FoodRequest).count() == 1
        assert db_session.query(User).count() == 1


def test_undefined_unit(db_session, no_users, no_food, default_units):
    with do_test_setup(db_session, no_users, no_food, default_units):
        user_reply = i18n.t('The food was not found, forwarding request to the owner')
        owner_reply = i18n.t('Please define unit for this food')
        create_food(db_session, i18n.get('locale'), 'Chicken soup',
                    0.36, 0.012, 0.035, 0.025)
        create_unit(db_session, i18n.get('locale'), 'bowl')
        user = get_or_create_user(db_session, 12345)
        tid = str(user.telegram_id)
        owner_id = os.getenv('OWNER_TELEGRAM_ID')
        messages = food_entry(db_session, user,
                              'Chicken soup 1 bowl')
        assert tid in messages
        assert owner_id in messages
        assert messages[tid] == user_reply
        assert owner_reply in messages[owner_id]
        assert db_session.query(FoodLog).count() == 0
        assert db_session.query(FoodRequest).count() == 1
        assert db_session.query(User).count() == 1


def test_success(db_session, no_users, no_food, default_units):
    with do_test_setup(db_session, no_users, no_food, default_units):
        food = create_food(db_session, i18n.get('locale'), 'Chicken soup',
                           0.36, 0.012, 0.035, 0.025)
        unit = create_unit(db_session, i18n.get('locale'), 'bowl')
        define_unit_for_food(db_session, food, unit, 350, False)
        user = get_or_create_user(db_session, 12345)
        tid = str(user.telegram_id)
        owner_id = os.getenv('OWNER_TELEGRAM_ID')
        messages = food_entry(db_session, user,
                              'Chicken soup 1 bowl')
        assert tid in messages
        assert owner_id in messages
        assert i18n.t('Food added') in messages[tid]
        assert i18n.t('Food added') in messages[owner_id]
        assert db_session.query(FoodLog).count() == 1
        assert db_session.query(FoodRequest).count() == 0
        assert db_session.query(User).count() == 1

        user = get_or_create_user(db_session, 12345)
        food_log = db_session.query(FoodLog).one()
        assert food_log.user_id == user.id
        assert food_log.food_id == food.id
        assert food_log.unit_id == unit.id
        assert food_log.date.strftime('%Y-%m-%d') == date_now()
        assert food_log.calories == 126  # 36 * 350 / 100
        assert food_log.fat == 4.2
        assert food_log.carbs == 12.25
        assert food_log.protein == 8.75

        messages = food_entry(db_session, user, 'Chicken soup 150 g')
        assert tid in messages
        assert owner_id in messages
        assert i18n.t('Food added') in messages[tid]
        assert i18n.t('Food added') in messages[owner_id]
        assert db_session.query(FoodLog).count() == 2
        assert db_session.query(FoodRequest).count() == 0
        assert db_session.query(User).count() == 1

        food_log = db_session.query(FoodLog).order_by(desc('id')).first()
        assert food_log.user_id == user.id
        assert food_log.food_id == food.id
        assert food_log.unit_id == get_gram_unit(db_session).id
        assert food_log.date.strftime('%Y-%m-%d') == date_now()
        assert food_log.calories == 54  # 36 * 150 / 100
        assert food_log.fat == 1.8
        assert food_log.carbs == 5.25
        assert food_log.protein == 3.75

        # testing default unit (g)
        messages = food_entry(db_session, user, 'Chicken soup 120')
        assert tid in messages
        assert owner_id in messages
        assert i18n.t('Food added') in messages[tid]
        assert i18n.t('Food added') in messages[owner_id]
        assert db_session.query(FoodLog).count() == 3

        food_log = db_session.query(FoodLog).order_by(desc('id')).first()
        assert food_log.unit_id == get_gram_unit(db_session).id
        assert food_log.date.strftime('%Y-%m-%d') == date_now()
        assert food_log.calories == 43.2  # 36 * 120 / 100
        assert food_log.fat == 1.44
        assert food_log.carbs == 4.2
        assert food_log.protein == 3
