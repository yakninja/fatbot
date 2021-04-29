import logging
import os
import re

import i18n
from sqlalchemy.orm import sessionmaker, Session
from telegram import Update
from telegram.ext import CallbackContext

from db import db_engine
from exc import FoodNotFound, UnitNotFound, UnitNotDefined
from models import FoodRequest, User, WeightLog
from models.core import get_or_create_user, log_food, food_log_message

logger = logging.getLogger(__name__)

WEIGHT_ENTRY_PATTERN = re.compile('^/weight\\s+([0-9.,]+)$')


def weight_entry(db_session: Session, user: User, input_message: str) -> dict:
    """
    :param db_session:
    :param user:
    :param input_message:
    :return: dictionary {telegram_id: message}
    """
    user_tid = str(user.telegram_id)
    owner_tid = os.getenv('OWNER_TELEGRAM_ID')
    m = WEIGHT_ENTRY_PATTERN.match(input_message)
    if not m:
        return {user_tid: i18n.t('I don\'t understand')}
    try:
        weight = float(m.groups()[0].strip().replace(',', '.'))
        if weight <= 0:
            return {user_tid: i18n.t('I don\'t understand')}
    except (IndexError, AttributeError):
        return {user_tid: i18n.t('I don\'t understand')}

    db_session.add(WeightLog(user_id=user.id, weight=weight))
    db_session.commit()

    message = i18n.t('Weight recorded: %{weight}', weight='{:.1f}'.format(weight))

    return {user_tid: message, owner_tid: message}


def weight_entry_command(update: Update, _: CallbackContext) -> None:
    """
    Process weight entry, echo it to the owner for debugging
    :param update:
    :param _:
    :return:
    """
    db_session = sessionmaker(bind=db_engine)()
    from_user = update.message.from_user
    owner_tid = os.getenv('OWNER_TELEGRAM_ID')

    info = "{} {}: {}".format(from_user.id, from_user.username, update.message.text)
    logger.info(info)
    _.bot.send_message(owner_tid, info)

    user = get_or_create_user(db_session, from_user.id)
    messages = weight_entry(db_session, user, update.message.text)
    for tid in messages.keys():
        _.bot.send_message(tid, messages[tid])