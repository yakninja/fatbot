from contextlib import contextmanager

import i18n
from commands.router import router
from commands import weight_entry_command, food_entry_command, today_command, cancel_command


@contextmanager
def do_test_setup(db_session, no_users):
    yield


def test_router(db_session, no_users):
    with do_test_setup(db_session, no_users):
        assert i18n.t('weight %{weight}', weight=50.5) == 'weight 50.5'
        data = [
            # weight entry
            ('/weight {}'.format(50.5), weight_entry_command),
            (i18n.t('weight %{weight}', weight=50.5), weight_entry_command),
            (i18n.t('weight %{weight}', weight=50.5).capitalize(), weight_entry_command),

            # food entry
            (i18n.t('Apple'), food_entry_command),
            (i18n.t('Apple 1'), food_entry_command),
            (i18n.t('Apple 1.6 g'), food_entry_command),
            (i18n.t('Apple 1,1 cup'), food_entry_command),
            (i18n.t('Chicken soup 2/3 bowl'), food_entry_command),

            # stats
            ('/today', today_command),
            (i18n.t('today'), today_command),
            (i18n.t('toDay'), today_command),

            # cancel
            ('/cancel', cancel_command),
            (i18n.t('cancel'), cancel_command),
            (i18n.t('Cancel'), cancel_command),
        ]
        for row in data:
            assert row[1] == router(row[0]), 'Failed for {}'.format(row[0])
