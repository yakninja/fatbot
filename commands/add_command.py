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
from models.food_unit import FoodUnit
from models.unit import Unit
from models.unit_name import UnitName
from models.user import get_or_create_user
from util import send_food_log

logger = logging.getLogger(__name__)

ADD_COMMAND_PATTERN = re.compile(
    '^/add\s*"(.+?)"\s+' +
    '"(.+?)"\s+' +
    'grams:([0-9.]+)\s+' +
    'cal:([0-9.]+)\s+' +
    'carb:([0-9.]+)\s+' +
    'fat:([0-9.]+)\s+' +
    'protein:([0-9.]+)' +
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
    unit_name_str = m.groups()[1].strip()
    grams = float(m.groups()[2].strip())

    unit_name = db_session.query(UnitName).filter_by(
        name=unit_name_str, language=i18n.get('locale')).first()
    gram_unit_name = db_session.query(UnitName).filter_by(
        name='g', language='en').first()
    if not unit_name:
        unit = Unit()
        db_session.add(unit)
        db_session.commit()
        unit_name = UnitName(unit_id=unit.id,
                             name=unit_name_str, language=i18n.get('locale'))
        db_session.add(unit_name)
        db_session.commit()
    else:
        unit = unit_name.unit

    calories = float(m.groups()[3])
    carbs = float(m.groups()[4])
    fat = float(m.groups()[5])
    protein = float(m.groups()[6])
    try:
        request_id = int(m.groups()[8])
    except IndexError:
        request_id = None

    food = Food(calories=calories, carbs=carbs, fat=fat, protein=protein,
                default_unit="g", g_per_unit=1  # deprecated, remove
                )
    db_session.add(food)
    db_session.commit()
    food_name = FoodName(food_id=food.id, name=name, language=i18n.get('locale'))
    db_session.add(food_name)
    db_session.commit()
    food_unit = FoodUnit(food_id=food.id, unit_id=unit.id,
                         is_default=True, grams=grams)
    db_session.add(food_unit)
    db_session.commit()

    if unit.id != gram_unit_name.unit_id:
        # also add in grams
        gram_food_unit = FoodUnit(food_id=food.id, unit_id=gram_unit_name.unit_id,
                                  is_default=False, grams=1)
        db_session.add(gram_food_unit)
        db_session.commit()

    _.bot.send_message(OWNER_USER_ID, i18n.t('Food added'))

    if request_id:
        logger.info('Request id: {}'.format(request_id))
        food_request = db_session.query(FoodRequest).filter_by(id=request_id).first()
        if not food_request:
            logger.info('Request not found')
            return
        food_log = log_food(food_request.user, food, unit, food_request.qty)
        send_food_log(_.bot, food_log)
    else:
        logger.info('Request id not set')
