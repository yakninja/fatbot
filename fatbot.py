#!/usr/bin/env python
import logging
import os
import re

import i18n
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

from commands import *

logger = logging.getLogger(__name__)

i18n.load_path.append('./translations')
i18n.set('filename_format', '{locale}.{format}')
i18n.set('skip_locale_root_data', True)
i18n.set('locale', 'ru')
i18n.set('fallback', 'en')

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OWNER_TELEGRAM_ID = os.getenv('OWNER_TELEGRAM_ID')


def start_command(update: Update, _: CallbackContext) -> None:
    """Greet the user on /start"""
    update.message.reply_text(i18n.t('Hi!'))


def main() -> None:
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
    )
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TELEGRAM_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("settings", settings_command))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("day", day_command))

    # admin commands
    dispatcher.add_handler(CommandHandler("add_food", add_food_command))
    dispatcher.add_handler(CommandHandler("add_unit", add_unit_command))
    dispatcher.add_handler(CommandHandler("define_unit", define_unit_command))

    # default command: food entry
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, food_entry_command))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
