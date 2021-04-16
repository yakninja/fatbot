import logging
import os
import re

import i18n
from telegram import Update
from telegram.ext import CallbackContext

# Oatmeal 100 g
# Apple 1
from db import db_session
from models.food_log import log_food
from models.food_name import FoodName
from models.food_request import FoodRequest
from models.food_unit import FoodUnit
from models.unit_name import UnitName
from models.user import get_or_create_user
from util import send_food_log

FOOD_ENTRY_PATTERN = re.compile("^(.+?)\s+([0-9.,]+)?(\s+.+)?\s*$")

logger = logging.getLogger(__name__)

OWNER_USER_ID = os.getenv('OWNER_USER_ID')


def food_entry_command(update: Update, _: CallbackContext) -> None:
    info = "{} {}: {}".format(update.message.from_user.id, update.message.from_user.username, update.message.text)
    logger.info(info)
    _.bot.send_message(OWNER_USER_ID, info)

    user = get_or_create_user(update.message.from_user.id)

    # parse food entry
    m = FOOD_ENTRY_PATTERN.match(update.message.text)
    if not m:
        update.message.reply_text(i18n.t('I don\'t understand'))
        return

    name = m.groups()[0].strip()
    try:
        qty = float(m.groups()[1].strip().replace(',', '.'))
        if qty == 0:
            qty = 1  # default
    except (IndexError, AttributeError):
        qty = 1

    try:
        unit_name_str = m.groups()[2].strip()
    except (IndexError, AttributeError):
        unit_name_str = None

    food_name = db_session.query(FoodName).filter_by(name=name).first()
    if not food_name:
        food_request = FoodRequest(user_id=user.id, qty=qty,
                                   request=update.message.text)
        db_session.add(food_request)
        db_session.commit()
        n = db_session.query(UnitName).filter_by(
            name='g', language='en').first()
        gram_unit_name = db_session.query(UnitName).filter_by(
            unit_id=n.unit_id, language=i18n.get('locale')).first().name
        n = db_session.query(UnitName).filter_by(
            name='pc', language='en').first()
        pc_unit_name = db_session.query(UnitName).filter_by(
            unit_id=n.unit_id, language=i18n.get('locale')).first().name

        lines = [
            i18n.t('Please add new food'),
            '/add "{}" "{}" grams:100 cal:0.0 carb:0.0 fat:0.0 protein:0.0 req:{}'.format(
                name, gram_unit_name, food_request.id),
            i18n.t('or'),
            '/add "{}" "{}" grams:123 cal:0.0 carb:0.0 fat:0.0 protein:0.0 req:{}'.format(
                name, pc_unit_name, food_request.id),
        ]
        if unit_name_str is not None and unit_name_str != gram_unit_name and unit_name_str != pc_unit_name:
            lines.append(i18n.t('or'))
            lines.append('/add "{}" "{}" grams:100 cal:0.0 carb:0.0 fat:0.0 protein:0.0 req:{}'.format(
                name, unit_name_str, food_request.id))

        _.bot.send_message(OWNER_USER_ID, "\n".join(lines))
        update.message.reply_text(i18n.t('The food was not found, forwarding request to the owner'))
        return

    unit_name = None
    if unit_name_str:
        unit_name = db_session.query(UnitName).filter_by(
            name=unit_name_str, language=i18n.get('locale')).first()

    if not unit_name:
        default_food_unit = db_session.query(FoodUnit).filter_by(
            food_id=food_name.food.id, is_default=True).first()
        unit = default_food_unit.unit
    else:
        unit = unit_name.unit

    food_log = log_food(user, food_name.food, unit, qty)
    send_food_log(_.bot, food_log)
