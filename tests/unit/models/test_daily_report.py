import os
from datetime import datetime, timedelta
from contextlib import contextmanager

import pytest

from models import User, date_now
from models.core import create_food, create_unit, daily_report_message, define_unit_for_food, get_or_create_user, log_food

import i18n


@contextmanager
def do_test_setup(db_session, no_users, no_food, default_units):
    yield


def test_daily_report(db_session, no_users, no_food, default_units):
    with do_test_setup(db_session, no_users, no_food, default_units):
        assert len(db_session.query(User).all()) == 0

        today_date = date_now()
        user = get_or_create_user(db_session, telegram_id='12345')
        assert user is not None
        assert user.id is not None
        assert user.profile is not None
        assert user.daily_report is not None
        assert user.daily_report.last_report_date.strftime(
            '%Y-%m-%d') == today_date

        # no food logged yet
        assert daily_report_message(db_session=db_session,
                                    user=user, date=today_date) is None

        apple_food = create_food(db_session, 'en', 'Apple',
                                 calories=0.52, fat=0.002, carbs=0.14, protein=0.003)
        bread_food = create_food(db_session, 'en', 'Bread',
                                 calories=2.65, fat=0.032, carbs=0.49, protein=0.09)
        slice_unit = create_unit(db_session, 'en', 'slice')
        define_unit_for_food(db_session, bread_food,
                             slice_unit, grams=30, is_default=True)
        log_food(db_session, locale='en', user=user,
                 food_name='Bread', unit_name='slice', qty=2,
                 date=today_date)
        log_food(db_session, locale='en', user=user,
                 food_name='Apple', unit_name='g', qty=100,
                 date=today_date)

        # no food logged yesterday
        assert daily_report_message(
            db_session=db_session, user=user, date=today_date) is None

        today_date_obj = datetime.strptime(today_date, '%Y-%m-%d')
        tomorrow_date = (today_date_obj + timedelta(days=1)
                         ).strftime('%Y-%m-%d')

        report_message = daily_report_message(
            db_session=db_session, user=user, date=tomorrow_date)
        assert report_message is not None
        assert i18n.t('Time for your daily statistics!') in report_message
