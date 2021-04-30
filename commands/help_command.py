import i18n
from telegram import Update
from telegram.ext import CallbackContext


def help_command(update: Update, _: CallbackContext) -> None:
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
        i18n.t('/weight %{weight}', weight=50.5),
        i18n.t('or'),
        i18n.t('weight %{weight}', weight=50.5),
        '',
        '❌' + i18n.t('Removing your last entry:'),
        '',
        i18n.t('/cancel'),
        i18n.t('or'),
        i18n.t('cancel'),
        '',
        i18n.t('/day - show today stats'),
        i18n.t('/settings - show your settings'),
    ]
    update.message.reply_text("\n".join(help_strings))
