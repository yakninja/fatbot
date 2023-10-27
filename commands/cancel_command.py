import logging
import os
import re
import time

import i18n
from sqlalchemy import desc
from sqlalchemy.orm import sessionmaker, Session
from telegram import Update
from telegram.ext import ContextTypes

from db import db_engine
from exc import FoodNotFound, UnitNotFound, UnitNotDefined
from models import FoodRequest, User, WeightLog, CommandLog, FoodLog
from models.core import get_or_create_user, log_food, food_log_message

logger = logging.getLogger(__name__)


def get_cancel_pattern():
    """
    This depends on locale
    :return:
    """
    return re.compile('^(/cancel|{})$'.format(i18n.t('cancel')), re.I)


def cancel(db_session: Session, user: User, input_message: str) -> dict:
    """
    :param db_session:
    :param user:
    :param input_message:
    :return: dictionary {telegram_id: message}
    """
    user_tid = str(user.telegram_id)
    owner_tid = os.getenv('OWNER_TELEGRAM_ID')
    m = get_cancel_pattern().match(input_message)
    invalid_reply = {user_tid: i18n.t('I don\'t understand')}
    if not m:
        return invalid_reply
    command_log = db_session.query(CommandLog).filter_by(
        user_id=user.id).order_by(desc('id')).first()
    if not command_log:
        return {user_tid: i18n.t('Nothing to cancel')}

    if command_log.command_type == CommandLog.FOOD_ENTRY:
        entry = db_session.query(FoodLog).filter_by(
            user_id=user.id).order_by(desc('id')).first()
    elif command_log.command_type == CommandLog.WEIGHT_ENTRY:
        entry = db_session.query(WeightLog).filter_by(
            user_id=user.id).order_by(desc('id')).first()
    else:
        return {user_tid: i18n.t('Invalid command type')}

    if entry:
        db_session.delete(entry)

    db_session.delete(command_log)
    db_session.commit()
    message = i18n.t('Command cancelled: %{command}', command=command_log.command)
    return {user_tid: message, owner_tid: message}


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Cancel the latest command
    :param update:
    :param context:
    :return:
    """
    db_session = sessionmaker(bind=db_engine)()
    from_user = update.message.from_user
    owner_tid = os.getenv('OWNER_TELEGRAM_ID')

    info = "{} {}: {}".format(from_user.id, from_user.username, update.message.text)
    logger.info(info)
    await context.bot.send_message(owner_tid, info)

    user = get_or_create_user(db_session, from_user.id)
    if user is None:
        return
    messages = cancel(db_session, user, update.message.text)
    for tid in messages.keys():
        await context.bot.send_message(tid, messages[tid])
