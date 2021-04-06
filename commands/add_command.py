import logging
import os
import re

import i18n
from telegram import Update
from telegram.ext import CallbackContext
from datetime import datetime

from models.food import Food
from models.food_log import FoodLog, date_now, log_food
from db import db_session
from models.food_name import FoodName
from models.food_request import FoodRequest
from models.user import get_or_create_user
from util import send_food_log

logger = logging.getLogger(__name__)

ADD_COMMAND_PATTERN = re.compile(
    '^/add\s*"(.+?)"\s+"(.+?)"\s+' +
    'gunit:([0-9.]+)\s+'+
    'cal:([0-9.]+)\s+'+
    'carb:([0-9.]+)\s+'+
    'fat:([0-9.]+)\s+'+
    'prot:([0-9.]+)'+
    '(\s+req:([0-9]+))?\s*$'
)

OWNER_USER_ID = os.getenv('OWNER_USER_ID')


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
    request_id = int(m.groups()[8]) if 8 in m.groups() else None

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
