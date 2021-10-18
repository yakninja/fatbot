import os
from datetime import datetime, timedelta
from contextlib import contextmanager

import pytest
from sqlalchemy.sql.expression import text
from jobs.daily_report_job import daily_report_job

from models import DailyReport, FutureMessage, User, date_now
from models.core import create_food, create_unit, daily_report_message, define_unit_for_food, get_or_create_user, log_food

import i18n


@contextmanager
def do_test_setup(db_session, no_users, no_food, default_units):
    yield


def test_daily_report(db_session, no_users, no_food, default_units):
    with do_test_setup(db_session, no_users, no_food, default_units):
        assert len(db_session.query(User).all()) == 0
        assert len(db_session.query(FutureMessage).all()) == 0

        today_date = date_now()
        today_date_obj = datetime.strptime(today_date, '%Y-%m-%d')
        yesterday_date = (today_date_obj - timedelta(days=1)
                          ).strftime('%Y-%m-%d')

        user = get_or_create_user(db_session, telegram_id='12345')
        assert user is not None
        assert user.id is not None
        assert user.profile is not None
        assert user.daily_report is not None
        assert user.daily_report.last_report_date.strftime(
            '%Y-%m-%d') == today_date
        user.daily_report.last_report_date = yesterday_date
        db_session.add(user.daily_report)
        db_session.commit()
         
        user = get_or_create_user(db_session, telegram_id='12345')
        assert user.daily_report.last_report_date.strftime(
            '%Y-%m-%d') == yesterday_date
        assert db_session.query(DailyReport) \
            .filter(DailyReport.last_report_date < today_date).count() == 1

        # no food logged yet

        daily_report_job(db_session=db_session)
        assert len(db_session.query(FutureMessage).all()) == 0
        # last_report_date will reset to current date after this
        user.daily_report.last_report_date = yesterday_date
        db_session.add(user.daily_report)
        db_session.commit()

        create_food(db_session, 'en', 'Apple',
                    calories=0.52, fat=0.002, carbs=0.14, protein=0.003)
        log_food(db_session, locale='en', user=user,
                 food_name='Apple', unit_name='g', qty=100,
                 date=today_date)

        # no food logged yesterday
        daily_report_job(db_session=db_session)
        assert len(db_session.query(FutureMessage).all()) == 0
        # last_report_date will reset to current date after this
        user.daily_report.last_report_date = yesterday_date
        db_session.add(user.daily_report)
        db_session.commit()

        log_food(db_session, locale='en', user=user,
                 food_name='Apple', unit_name='g', qty=100,
                 date=yesterday_date)

        # now we get a report message queued
        report_message = daily_report_message(
            db_session=db_session, user=user, date=today_date)
        assert report_message is not None
        daily_report_job(db_session=db_session)
        assert len(db_session.query(FutureMessage).all()) == 1
