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
            '/add "{}" "g" gunit:1 cal:0.0 carb:0.0 fat:0.0 prot:0.0 req:{}'.format(name, food_request.id),
            i18n.t('or'),
            '/add "{}" "pc" gunit:100 cal:0.0 carb:0.0 fat:0.0 prot:0.0 req:{}'.format(name, food_request.id),
        ]
        _.bot.send_message(OWNER_USER_ID, "\n".join(lines))
        update.message.reply_text(i18n.t('The food was not found, forwarding request to the owner'))
        return

    food_log = log_food(user, food_name.food, qty)
    send_food_log(_.bot, food_log)
