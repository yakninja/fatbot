from telegram import Update
from telegram.ext import CallbackContext

from commands import weight_entry_command, food_entry_command


def router(command: str):
    """
    Choose command handler based on command content
    :param command:
    :return:
    """
    from commands.weight_entry_command import get_weight_entry_pattern
    print(command, get_weight_entry_pattern())
    if get_weight_entry_pattern().match(command):
        return weight_entry_command
    return food_entry_command


def router_command(update: Update, _: CallbackContext) -> None:
    func = router(update.message.text)
    return func(update, _)
