import os
from contextlib import contextmanager

import i18n
from sqlalchemy import desc

from commands.cancel_command import cancel
from commands.food_entry_command import food_entry
from commands.weight_entry_command import weight_entry
from models import User, CommandLog, WeightLog, FoodLog
from models.core import get_or_create_user, create_food


@contextmanager
def do_test_setup(db_session, no_food, no_users):
    yield


def test_cancel_last(db_session, no_food, no_users):
    with do_test_setup(db_session, no_food, no_users):
        assert db_session.query(User).count() == 0
        user = get_or_create_user(db_session, 12345)
        tid = str(user.telegram_id)
        owner_id = os.getenv('OWNER_TELEGRAM_ID')
        assert db_session.query(CommandLog).count() == 0
        create_food(db_session, i18n.get('locale'), 'Chicken soup',
                    0.36, 0.012, 0.035, 0.025)

        assert db_session.query(FoodLog).count() == 0
        food_entry(db_session, user, 'Chicken soup 100 g')
        assert db_session.query(CommandLog).count() == 1
        assert db_session.query(FoodLog).count() == 1

        command_log = db_session.query(CommandLog).order_by(desc('id')).first()
        assert command_log.command_type == CommandLog.FOOD_ENTRY
        assert command_log.command == 'Chicken soup 100 g'

        assert db_session.query(WeightLog).count() == 0
        weight_entry(db_session, user, "/weight 60.5")
        assert db_session.query(WeightLog).count() == 1
        assert db_session.query(CommandLog).count() == 2

        command_log = db_session.query(CommandLog).order_by(desc('id')).first()
        assert command_log.command_type == CommandLog.WEIGHT_ENTRY
        assert command_log.command == '/weight 60.5'

        messages = cancel(db_session, user, '/cancel')
        assert tid in messages
        assert owner_id in messages
        assert i18n.t('Command cancelled: %{command}', command='/weight 60.5') in messages[tid]
        assert db_session.query(WeightLog).count() == 0
        assert db_session.query(CommandLog).count() == 1
        assert db_session.query(FoodLog).count() == 1

        messages = cancel(db_session, user, '/cancel')
        assert tid in messages
        assert owner_id in messages
        assert i18n.t('Command cancelled: %{command}', command='Chicken soup 100 g') in messages[tid]
        assert db_session.query(WeightLog).count() == 0
        assert db_session.query(CommandLog).count() == 0
        assert db_session.query(FoodLog).count() == 0

        messages = cancel(db_session, user, '/cancel')
        assert tid in messages
        assert i18n.t('Nothing to cancel') == messages[tid]
