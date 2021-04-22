import logging
import os
import re

import i18n
from sqlalchemy.orm import sessionmaker
from telegram import Update
from telegram.ext import CallbackContext

from db import db_engine
from models import UnitName, Unit, FoodName, Food, FoodUnit, FoodRequest
from models.core import log_food

logger = logging.getLogger(__name__)

ADD_UPDATE_COMMAND_PATTERN = re.compile(
    '^/(add|update)\s*' +
    '"(.+?)"\s+' +
    '"(.+?)"\s+' +
    'grams:([0-9.]+)\s+' +
    'cal:([0-9.]+)\s+' +
    'carb:([0-9.]+)\s+' +
    'fat:([0-9.]+)\s+' +
    'protein:([0-9.]+)' +
    '(\s+req:([0-9]+))?\s*$'
)

OWNER_USER_ID = os.getenv('OWNER_USER_ID')


def add_update_command(update: Update, _: CallbackContext) -> None:
    db_session = sessionmaker(bind=db_engine)()
    info = "{} {}: {}".format(update.message.from_user.id, update.message.from_user.username, update.message.text)
    logger.info(info)
    if str(update.message.from_user.id) != str(OWNER_USER_ID):
        logger.info('Invalid sender: {} != {}'.format(update.message.from_user.id, OWNER_USER_ID))
        return
    m = ADD_UPDATE_COMMAND_PATTERN.match(update.message.text)
    if not m:
        update.message.reply_text(i18n.t('Invalid command format'))
        return

    command = m.groups()[0].strip()
    food_name_str = m.groups()[1].strip()

    food = None
    if command == 'update':
        food_name = db_session.query(FoodName).filter_by(
            name=food_name_str, language=i18n.get('locale')).first()
        if not food_name:
            update.message.reply_text(i18n.t('Food not found'))
            return
        food = food_name.food

    unit_name_str = m.groups()[2].strip()
    grams = float(m.groups()[3].strip())
    if grams == 0:
        update.message.reply_text(i18n.t('Invalid weight'))
        return

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

    calories = float(m.groups()[4]) / grams
    carbs = float(m.groups()[5]) / grams
    fat = float(m.groups()[6]) / grams
    protein = float(m.groups()[7]) / grams
    try:
        request_id = int(m.groups()[9])
    except IndexError:
        request_id = None

    if command == 'add':
        food = Food(calories=calories, carbs=carbs, fat=fat, protein=protein)
        db_session.add(food)
        db_session.commit()
        food_name = FoodName(food_id=food.id, name=food_name_str, language=i18n.get('locale'))
        db_session.add(food_name)
        db_session.commit()

    db_session.execute("""UPDATE food_unit SET is_default = 0
        WHERE food_id = :food_id""", {'food_id': food.id})
    food_unit = db_session.query(FoodUnit).filter_by(
        food_id=food.id, unit_id=unit.id).first()
    if not food_unit:
        food_unit = FoodUnit(food_id=food.id, unit_id=unit.id,
                             is_default=True, grams=grams)
        db_session.add(food_unit)
        db_session.commit()
    else:
        db_session.execute("""UPDATE food_unit SET is_default = 1
            WHERE food_id = :food_id AND unit_id = :unit_id""",
                           {'food_id': food.id, 'unit_id': unit.id})

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
        food_log = log_food(db_session, food_request.user, food, unit, food_request.qty)
        send_food_log(db_session, _.bot, food_log)
    else:
        logger.info('Request id not set')
