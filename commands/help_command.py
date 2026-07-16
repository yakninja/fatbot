import i18n
from telegram import Update
from telegram.ext import ContextTypes


async def help_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Usage
    :param update:
    :param _:
    :return:
    """
    help_strings = [
        '🥐' + i18n.t('Recording food:'),
        '',
        i18n.t('Apple 1'),
        i18n.t('or'),
        i18n.t('Oatmeal 100 g'),
        i18n.t('or'),
        i18n.t('Chicken soup 1 bowl'),
        '',
        '🪨' + i18n.t('Recording weight:'),
        '',
        '/weight {}'.format(50.5),
        i18n.t('or'),
        i18n.t('weight %{weight}', weight=50.5),
        '',
        '🏷️' + i18n.t('Weight chart labels:'),
        '',
        '/label 2026-07-16 Vacation',
        '/unlabel 2026-07-16',
        '',
        '❌' + i18n.t('Removing your last entry:'),
        '',
        '/cancel',
        i18n.t('or'),
        i18n.t('cancel'),
        '',
        '📊' + i18n.t('Day statistics:'),
        '',
        '/today',
        i18n.t('or'),
        i18n.t('today'),
        '',
        '⚙️' + i18n.t('Settings:'),
        '',
        '/settings',
    ]
    await update.message.reply_text("\n".join(help_strings))
