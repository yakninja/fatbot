import os
import shutil
import time
from contextlib import contextmanager

import i18n
from sqlalchemy import desc

from commands.weight_entry_command import weight_entry
from models import User, WeightLog
from models.core import get_or_create_user
from utils import TEMP_PATH


@contextmanager
def do_test_setup(db_session, no_users):
    if os.path.exists(TEMP_PATH):
        shutil.rmtree(TEMP_PATH)
    yield


def test_invalid_command(db_session, no_users):
    with do_test_setup(db_session, no_users):
        assert db_session.query(User).count() == 0
        user = get_or_create_user(db_session, 12345)
        assert user is not None
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
            assert 'message' in messages[tid]
            assert messages[tid]['message'] == i18n.t('I don\'t understand')


def test_valid_command(db_session, no_users):
    with do_test_setup(db_session, no_users):
        assert db_session.query(WeightLog).count() == 0
        user = get_or_create_user(db_session, 12345)
        assert user is not None
        tid = str(user.telegram_id)
        owner_id = os.getenv('OWNER_TELEGRAM_ID')

        data = [
            ('/weight 50', 50.0, 'Weight recorded: 50.0'),

            ('/weight 50.5', 50.5,
             i18n.t('Weight recorded: %{weight} (%{delta}, %{per_day} per day)',
                    weight=50.5, delta='+0.5', per_day='+0.07')),

            ('/weight 70,1', 70.1,
             i18n.t('Weight recorded: %{weight} (%{delta}, %{per_day} per day)',
                    weight=70.1, delta='+19.6', per_day='+2.80')),

            (i18n.t('weight %{weight}', weight=10.7), 10.7,
             i18n.t('Weight recorded: %{weight} (%{delta}, %{per_day} per day)',
                    weight=10.7, delta='-59.4', per_day='-8.49')),

            ("20.8", 20.8,
             i18n.t('Weight recorded: %{weight} (%{delta}, %{per_day} per day)',
                    weight=20.8, delta='+10.1', per_day='+1.44')),
        ]

        log_count = 1
        for row in data:
            command = row[0]
            weight = row[1]
            reply = row[2]
            messages = weight_entry(db_session, user, command)
            assert tid in messages
            assert owner_id in messages
            assert 'message' in messages[tid]
            assert 'message' in messages[owner_id]
            assert 'plot_file' in messages[tid]
            assert 'plot_file' in messages[owner_id]
            assert messages[tid]['message'] == reply
            assert messages[owner_id]['message'] == reply
            assert os.path.exists(messages[tid]['plot_file'])
            assert os.path.exists(messages[owner_id]['plot_file'])
            assert db_session.query(WeightLog).count() == log_count
            weight_log = db_session.query(
                WeightLog).order_by(desc('id')).first()
            assert weight_log.user_id == user.id
            assert weight_log.weight == weight
            log_count += 1
            db_session.execute(
                """UPDATE weight_log SET created_at = created_at - 86400 * 7""")
            db_session.commit()

        db_session.execute("""DELETE FROM weight_log""")
        db_session.commit()

        month_ago = time.time() - 86400 * 30
        week_ago = time.time() - 86400 * 7
        day_ago = time.time() - 86400
