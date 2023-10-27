import logging
import os
import re
import shlex

import i18n
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import sessionmaker, Session
from telegram import Update
from telegram.ext import ContextTypes

from commands.food_entry_command import food_entry
from db import db_engine
from exc import FoodNotFound
from models import UnitName, Unit, FoodName, Food, FoodUnit, FoodRequest, User
from models.core import log_food, get_food_by_name, create_food, define_unit_for_food, get_gram_unit, \
    get_or_create_user, get_unit_by_name, create_unit
from argumentparser import ArgumentParser

logger = logging.getLogger(__name__)

add_unit_parser = ArgumentParser(description=i18n.t('Add a unit record'))
add_unit_parser.add_argument('command_name', type=str, help=i18n.t('Command name'))
add_unit_parser.add_argument('unit_name', type=str, help=i18n.t('Unit name'))


def parse_add_unit_message(message: str):
    """
    Parses command message
    :param message:
    :return:
    """
    parts = shlex.split(message)
    params = vars(add_unit_parser.parse_args(parts))
    if params['command_name'] != '/add_unit':
        raise ValueError(i18n.t('Invalid command format'))
    del (params['command_name'])
    return params


def add_unit(db_session: Session, user: User, input_message: str) -> dict:
    """
    :param db_session:
    :param user:
    :param input_message:
    :return: dictionary {telegram_id: message}
    """
    user_tid = str(user.telegram_id)
    owner_tid = os.getenv('OWNER_TELEGRAM_ID')

    try:
        params = parse_add_unit_message(input_message)
    except ValueError:
        return {user_tid: i18n.t('Invalid command format')}

    if user_tid != owner_tid:
        return {user_tid: i18n.t('Invalid user id')}

    try:
        get_unit_by_name(db_session, i18n.get('locale'), params['unit_name'])
        return {user_tid: i18n.t('Unit already exists')}
    except NoResultFound:
        pass

    create_unit(db_session, locale=i18n.get('locale'), unit_name=params['unit_name'])

    return {user_tid: i18n.t('Unit added')}


async def add_unit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Add unit command (only for owner)
    /add_unit "Unit name"
    :param update:
    :param context:
    :return:
    """
    db_session = sessionmaker(bind=db_engine)()
    from_user = update.message.from_user

    info = "{} {}: {}".format(from_user.id, from_user.username, update.message.text)
    logger.info(info)

    user = get_or_create_user(db_session, from_user.id)
    if user is None:
        return
    messages = add_unit(db_session, user, update.message.text)
    for tid in messages.keys():
        await context.bot.send_message(tid, messages[tid])
