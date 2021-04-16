from contextlib import contextmanager

import pytest

from models import User
from models.core import get_or_create_user


@contextmanager
def do_test_setup(db_session, no_users):
    yield


def test_create_user(db_session, no_users):
    with do_test_setup(db_session, no_users):
        assert len(db_session.query(User).all()) == 0

        user = get_or_create_user(db_session, telegram_id='12345')
        assert user.id is not None
        assert user.profile is not None
        assert user.telegram_id == 12345
        assert user.profile.daily_calories > 0
        assert user.profile.daily_fat > 0
        assert user.profile.daily_carbs > 0
        assert user.profile.daily_protein > 0

