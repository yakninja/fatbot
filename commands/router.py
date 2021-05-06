import re

import i18n
from telegram import Update
from telegram.ext import CallbackContext

from commands import weight_entry_command, food_entry_command, today_command, cancel_command
from commands.weight_entry_command import get_weight_entry_pattern


def router(command: str):
    """
    Choose command handler based on command content
    :param command:
    :return:
    """
    command = command.strip().lower()
    if command in ['/today', i18n.t('today')]:
        return today_command
    if command in ['/cancel', i18n.t('cancel')]:
        return cancel_command
    if get_weight_entry_pattern().match(command):
        return weight_entry_command
    return food_entry_command


def router_command(update: Update, _: CallbackContext) -> None:
    func = router(update.message.text)
    return func(update, _)
