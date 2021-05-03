import os
from contextlib import contextmanager

import i18n
from sqlalchemy import desc

from commands.weight_entry_command import weight_entry
from models import User, WeightLog
from models.core import get_or_create_user


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

        data = [
            ('/weight 50', 50.0),
            ('/weight 50.5', 50.5),
            ('/weight 70,1', 70.1),
            (i18n.t('weight %{weight}', weight=100.7), 100.7),
        ]

        log_count = 1
        for row in data:
            command = row[0]
            weight = row[1]
            messages = weight_entry(db_session, user, command)
            assert tid in messages
            assert owner_id in messages
            assert messages[tid] == i18n.t('Weight recorded: %{weight}', weight=weight)
            assert messages[owner_id] == i18n.t('Weight recorded: %{weight}', weight=weight)
            assert db_session.query(WeightLog).count() == log_count
            weight_log = db_session.query(WeightLog).order_by(desc('id')).first()
            assert weight_log.user_id == user.id
            assert weight_log.weight == weight
            log_count += 1
