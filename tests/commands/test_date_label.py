import os
import shutil
import time
from contextlib import contextmanager
from datetime import datetime

import i18n

from commands.date_label_command import MAX_LABEL_LENGTH, date_label
from models import DateLabel, User, WeightLog
from models.core import get_or_create_user
from utils import TEMP_PATH


@contextmanager
def do_test_setup(db_session, no_users):
    if os.path.exists(TEMP_PATH):
        shutil.rmtree(TEMP_PATH)
    os.environ['OWNER_TELEGRAM_ID'] = '111222333'
    yield


def create_weight_logs(db_session, user):
    now = int(time.time())
    db_session.add(WeightLog(user_id=user.id, created_at=now - 86400 * 7, weight=70.0))
    db_session.add(WeightLog(user_id=user.id, created_at=now, weight=71.0))
    db_session.commit()
    return datetime.fromtimestamp(now).strftime('%Y-%m-%d')


def test_add_and_remove_date_label_redraw_charts(db_session, no_users):
    with do_test_setup(db_session, no_users):
        assert db_session.query(User).count() == 0
        user = get_or_create_user(db_session, 12345)
        tid = str(user.telegram_id)
        owner_id = os.getenv('OWNER_TELEGRAM_ID')
        label_date = create_weight_logs(db_session, user)

        messages = date_label(db_session, user, '/label {} Vacation'.format(label_date))

        assert db_session.query(DateLabel).count() == 1
        saved_label = db_session.query(DateLabel).one()
        assert saved_label.user_id == user.id
        assert saved_label.label_date.strftime('%Y-%m-%d') == label_date
        assert saved_label.label == 'Vacation'
        assert messages[tid]['message'] == i18n.t(
            'Date label saved: %{date} %{label}',
            date=label_date,
            label='Vacation',
        )
        assert os.path.exists(messages[tid]['plot_file'])
        assert os.path.exists(messages[owner_id]['plot_file'])

        messages = date_label(db_session, user, '/unlabel {}'.format(label_date))

        assert db_session.query(DateLabel).count() == 0
        assert messages[tid]['message'] == i18n.t(
            'Date label removed: %{date} %{label}',
            date=label_date,
            label='Vacation',
        )
        assert os.path.exists(messages[tid]['plot_file'])
        assert os.path.exists(messages[owner_id]['plot_file'])


def test_date_label_validates_label_length(db_session, no_users):
    with do_test_setup(db_session, no_users):
        user = get_or_create_user(db_session, 12345)
        label_date = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d')
        messages = date_label(
            db_session,
            user,
            '/label {} {}'.format(label_date, 'x' * (MAX_LABEL_LENGTH + 1)),
        )

        assert messages[str(user.telegram_id)]['message'] == i18n.t(
            'Date label must be %{count} characters or fewer',
            count=MAX_LABEL_LENGTH,
        )
        assert db_session.query(DateLabel).count() == 0
