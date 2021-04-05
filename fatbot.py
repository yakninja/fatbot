#!/usr/bin/env python
import logging
import os
import re

import i18n
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

from db import get_db_url
from models.food import Food
from models.food_log import FoodLog
from models.food_name import FoodName
from models.food_request import FoodRequest
from models.user import User
from models.user_profile import UserProfile

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

i18n.load_path.append('./translations')
i18n.set('filename_format', '{locale}.{format}')
i18n.set('skip_locale_root_data', True)
i18n.set('locale', 'ru')
i18n.set('fallback', 'en')

db_engine = create_engine(get_db_url())
db_session = sessionmaker(bind=db_engine)()

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
OWNER_USER_ID = os.environ['OWNER_USER_ID']


def start_command(update: Update, _: CallbackContext) -> None:
    """Greet the user on /start"""
    update.message.reply_text(i18n.t('Hi!'))


def help_command(update: Update, _: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    help_strings = [
        i18n.t('Usage:'),
    ]
    update.message.reply_text("\n".join(help_strings))


# Oatmeal 100 g
# Apple 1
FOOD_ENTRY_PATTERN = re.compile("^(.+?)\s+([0-9.,]+)?(\s+.+)?\s*$")


def food_entry_command(update: Update, _: CallbackContext) -> None:
    info = "{} {}: {}".format(update.message.from_user.id, update.message.from_user.username, update.message.text)
    logger.info(info)
    _.bot.send_message(OWNER_USER_ID, info)

    telegram_id = update.message.from_user.id
    user = db_session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id)
        db_session.add(user)
        db_session.commit()
        # TODO: configure calories etc. See https://www.calculator.net/macro-calculator.html
        profile = UserProfile(user_id=user.id,
                              daily_calories=1538,
                              daily_carbs=205,
                              daily_fat=44,
                              daily_protein=94)
        db_session.add(profile)
        db_session.commit()

    # parse food entry
    m = FOOD_ENTRY_PATTERN.match(update.message.text)
    if not m:
        update.message.reply_text(i18n.t('I don\'t understand'))
        return

    name = m.groups()[0].strip()
    qty = float(m.groups()[1].strip().replace(',', '.'))
    if qty == 0:
        qty = 100  # default
    food_name = db_session.query(FoodName).filter_by(name=name).first()
    if not food_name:
        food_request = FoodRequest(user_id=user.id, qty=qty, request=update.message.text)
        db_session.add(food_request)
        db_session.commit()
        lines = [
            i18n.t('Please add new food'),
            '/add "{}" "g" gunit:100 cal:0.0 carb:0.0 fat:0.0 prot:0.0 req:{}'.format(name, food_request.id)
        ]
        _.bot.send_message(OWNER_USER_ID, "\n".join(lines))
        update.message.reply_text(i18n.t('The food was not found, forwarding request to the owner'))
        return

    food_log = log_food(user, food_name.food, qty)
    send_food_log(_.bot, food_log)


ADD_COMMAND_PATTERN = re.compile(
    '^/add\s*"(.+?)"\s+"(.+?)"\s+gunit:([0-9.]+)\s+cal:([0-9.]+)\s+carb:([0-9.]+)\s+fat:([0-9.]+)\s+prot:([0-9.]+)(\s+req:([0-9]+))?\s*$'
)


def add_command(update: Update, _: CallbackContext) -> None:
    info = "{} {}: {}".format(update.message.from_user.id, update.message.from_user.username, update.message.text)
    logger.info(info)
    if str(update.message.from_user.id) != str(OWNER_USER_ID):
        logger.info('Invalid sender: {} != {}'.format(update.message.from_user.id, OWNER_USER_ID))
        return
    m = ADD_COMMAND_PATTERN.match(update.message.text)
    if not m:
        update.message.reply_text(i18n.t('Invalid command format'))
        return
    name = m.groups()[0].strip()
    default_unit = m.groups()[1].strip()
    g_per_unit = float(m.groups()[2].strip())
    calories = float(m.groups()[3])
    carbs = float(m.groups()[4])
    fat = float(m.groups()[5])
    protein = float(m.groups()[6])
    request_id = int(m.groups()[8])

    food = Food(calories=calories, carbs=carbs, fat=fat, protein=protein,
                default_unit=default_unit, g_per_unit=g_per_unit)
    db_session.add(food)
    db_session.commit()
    food_name = FoodName(food_id=food.id, name=name, language=i18n.get('locale'))
    db_session.add(food_name)
    db_session.commit()
    _.bot.send_message(OWNER_USER_ID, i18n.t('Food added'))

    if request_id:
        food_request = db_session.query(FoodRequest).filter_by(id=request_id).first()
        if not food_request:
            return
        food_log = log_food(food_request.user, food, food_request.qty)
        send_food_log(_.bot, food_log)


def send_food_log(bot, food_log: FoodLog):
    user_profile = food_log.user.profile
    query = db_session.query(
        FoodLog.date,
        func.sum(FoodLog.calories).label('calories'),
        func.sum(FoodLog.carbs).label('carbs'),
        func.sum(FoodLog.fat).label('fat'),
        func.sum(FoodLog.protein).label('protein')
    ).filter_by(user_id=food_log.user_id, date=food_log.date).first()

    calories_left = "{:.2f}".format(max(0, user_profile.daily_calories - query['calories']))
    fat_left = "{:.2f}".format(max(0, user_profile.daily_fat - query['fat']))
    carbs_left = "{:.2f}".format(max(0, user_profile.daily_carbs - query['carbs']))
    protein_left = "{:.2f}".format(max(0, user_profile.daily_protein - query['protein']))

    lines = [
        i18n.t('Food recorded'),
        i18n.t('Calories: %{calories} / %{calories_left}', calories=food_log.calories, calories_left=calories_left),
        i18n.t('Fat: %{fat} / %{fat_left}', fat=food_log.fat, fat_left=fat_left),
        i18n.t('Carbs: %{carbs} / %{carbs_left}', carbs=food_log.carbs, carbs_left=carbs_left),
        i18n.t('Protein: %{protein} / %{protein_left}', protein=food_log.protein, protein_left=protein_left),
    ]
    message = "\n".join(lines)
    bot.send_message(food_log.user.telegram_id, message)
    bot.send_message(OWNER_USER_ID, message)
    logger.info(message)


def log_food(user: User, food: Food, qty: float) -> FoodLog:
    """
    Oatmeal 50 = Oatmeal 100 g * (1 (g_per_unit) * 50 / 100)
    Apple 1 = Apple 100 g * (182 (g_per_unit) * 1 / 100)
    :param user:
    :param food:
    :param qty:
    :return:
    """
    multiplier = qty * food.g_per_unit / 100
    food_log = FoodLog(user_id=user.id, food_id=food.id, qty="{:.2f}".format(qty),
                       calories="{:.2f}".format(food.calories * multiplier),
                       carbs="{:.2f}".format(food.carbs * multiplier),
                       fat="{:.2f}".format(food.fat * multiplier),
                       protein="{:.2f}".format(food.protein * multiplier)
                       )
    db_session.add(food_log)
    db_session.commit()
    return food_log


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TELEGRAM_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("add", add_command))

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
