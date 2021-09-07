import logging
import os
import shlex

import i18n
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import sessionmaker, Session
from telegram import Update
from telegram.ext import CallbackContext

from commands.food_entry_command import food_entry
from db import db_engine
from models import FoodRequest, User, FoodUnit
from models.core import get_food_by_name, define_unit_for_food, get_gram_unit, get_or_create_user, \
    get_unit_by_name
from parser import ArgumentParser, str2bool

logger = logging.getLogger(__name__)

define_unit_parser = ArgumentParser(description=i18n.t('Define unit for food'))
define_unit_parser.add_argument('command_name', type=str, help=i18n.t('Command name'))
define_unit_parser.add_argument('food_name', type=str, help=i18n.t('Food name'))
define_unit_parser.add_argument('unit_name', type=str, help=i18n.t('Unit name'))
define_unit_parser.add_argument('--grams', type=float, help=i18n.t('Grams per unit'), required=True)
define_unit_parser.add_argument('--default', type=str2bool, nargs='?', const=True,
                                default=False, help=i18n.t('Default unit for this food'))
define_unit_parser.add_argument('--request', type=int, help=i18n.t('Request ID'), required=False)


def parse_define_unit_message(message: str):
    """
    Parses define_unit command message
    :param message:
    :return: dictionary with food name, unit name, grams and optionally food request id
    """
    parts = shlex.split(message)
    params = vars(define_unit_parser.parse_args(parts))
    if params['command_name'] != '/define_unit':
        raise ValueError(i18n.t('Invalid command format'))
    del (params['command_name'])
    return params


def define_unit(db_session: Session, user: User, input_message: str) -> dict:
    """
    /define_unit food_name unit_name --grams=... --default=... --request=...
    :param db_session:
    :param user:
    :param input_message:
    :return: dictionary {telegram_id: message} Messages which you need to send
    """
    user_tid = str(user.telegram_id)
    owner_tid = os.getenv('OWNER_TELEGRAM_ID')

    try:
        params = parse_define_unit_message(input_message)
    except ValueError:
        return {user_tid: i18n.t('Invalid command format')}

    if user_tid != owner_tid:
        return {user_tid: i18n.t('Invalid user id')}

    try:
        food = get_food_by_name(db_session, i18n.get('locale'), params['food_name'])
    except NoResultFound:
        return {user_tid: i18n.t('Food does not exist')}

    try:
        unit = get_unit_by_name(db_session, i18n.get('locale'), params['unit_name'])
    except NoResultFound:
        # todo: implicitly add this unit
        return {user_tid: i18n.t('Unit does not exist')}

    # check if gram unit defined (must be)
    gram_unit = get_gram_unit(db_session)
    food_unit = db_session.query(FoodUnit).filter_by(food_id=food.id, unit_id=gram_unit.id).first()
    if not food_unit:
        define_unit_for_food(db_session, food, gram_unit, 1.0, True)

    define_unit_for_food(db_session, food, unit, params['grams'], params['default'])

    request_id = params['request']
    if request_id:
        request = db_session.query(FoodRequest).get(request_id)
        if request:
            # now when unit is defined, repeat the request
            messages = food_entry(db_session, request.user, request.request)
            messages[owner_tid] = i18n.t('Unit defined') + "\n" + messages[owner_tid]
            return messages
    return {user_tid: i18n.t('Unit defined')}


def define_unit_command(update: Update, _: CallbackContext) -> None:
    """
    Define unit command (only for owner)
    /define_unit "Food name" "Unit name" --grams=... --request=...
    Food name, unit name and grams are required, the rest values are optional

    :param update:
    :param _:
    :return:
    """
    db_session = sessionmaker(bind=db_engine)()
    from_user = update.message.from_user

    info = "{} {}: {}".format(from_user.id, from_user.username, update.message.text)
    logger.info(info)

    user = get_or_create_user(db_session, from_user.id)
    if user is None:
        return
    messages = define_unit(db_session, user, update.message.text)
    for tid in messages.keys():
        _.bot.send_message(tid, messages[tid])
