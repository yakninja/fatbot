import logging
import os
import re
import shlex

import i18n
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import sessionmaker, Session
from telegram import Update
from telegram.ext import CallbackContext

from commands.food_entry_command import food_entry
from db import db_engine
from exc import FoodNotFound
from models import UnitName, Unit, FoodName, Food, FoodUnit, FoodRequest, User
from models.core import log_food, get_food_by_name, create_food, define_unit_for_food, get_gram_unit, get_or_create_user
from parser import ArgumentParser

logger = logging.getLogger(__name__)

add_food_parser = ArgumentParser(description=i18n.t('Add a food record'))
add_food_parser.add_argument('command_name', type=str, help=i18n.t('Command name'))
add_food_parser.add_argument('food_name', type=str, help=i18n.t('Food name'))
add_food_parser.add_argument('--calories', type=float, help=i18n.t('Calories per 100 g'), required=True)
add_food_parser.add_argument('--carbs', type=float, help=i18n.t('Carbs per 100 g'),
                             default=0.0, required=False)
add_food_parser.add_argument('--fat', type=float, help=i18n.t('Fat per 100 g'),
                             default=0.0, required=False)
add_food_parser.add_argument('--protein', type=float, help=i18n.t('Protein per 100 g'),
                             default=0.0, required=False)
add_food_parser.add_argument('--request', type=int, help=i18n.t('Request ID'), required=False)


def parse_add_food_message(message: str):
    """
    Parses command message
    :param message:
    :return: dictionary with food name, values and optionally food request id (see regex pattern)
    """
    parts = shlex.split(message)
    params = vars(add_food_parser.parse_args(parts))
    if params['command_name'] != '/add_food':
        raise ValueError(i18n.t('Invalid command format'))
    del (params['command_name'])
    return params


def add_food(db_session: Session, user: User, input_message: str) -> dict:
    """
    :param db_session:
    :param user:
    :param input_message:
    :return: dictionary {telegram_id: message}
    """
    user_tid = str(user.telegram_id)
    owner_tid = os.getenv('OWNER_TELEGRAM_ID')

    try:
        params = parse_add_food_message(input_message)
    except ValueError:
        return {user_tid: i18n.t('Invalid command format')}

    if user_tid != owner_tid:
        return {user_tid: i18n.t('Invalid user id')}

    try:
        get_food_by_name(db_session, i18n.get('locale'), params['food_name'])
        return {user_tid: i18n.t('Food already exists')}
    except NoResultFound:
        pass

    food = create_food(db_session, locale=i18n.get('locale'),
                       food_name=params['food_name'],
                       calories=params['calories'] / 100,
                       fat=params['fat'] / 100,
                       carbs=params['carbs'] / 100,
                       protein=params['protein'] / 100)
    define_unit_for_food(db_session, food, get_gram_unit(db_session), 1.0, True)

    request_id = params['request']
    if request_id:
        request = db_session.query(FoodRequest).get(request_id)
        if request:
            # now when food is added, repeat the request
            messages = food_entry(db_session, request.user, request.request)
            messages[owner_tid] = i18n.t('Food added') + "\n" + messages[owner_tid]
            return messages
    return {user_tid: i18n.t('Food added')}


def add_food_command(update: Update, _: CallbackContext) -> None:
    """
    Add food command (only for owner ATM). Calories etc are per 100 g
    /add_food "Food name" --calories=... --fat=... --carbs=... --protein=...
        --request=...
    Food name and calories are required, the rest values are optional

    :param update:
    :param _:
    :return:
    """
    db_session = sessionmaker(bind=db_engine)()
    from_user = update.message.from_user

    info = "{} {}: {}".format(from_user.id, from_user.username, update.message.text)
    logger.info(info)

    user = get_or_create_user(db_session, from_user.id)
    messages = add_food(db_session, user, update.message.text)
    for tid in messages.keys():
        _.bot.send_message(tid, messages[tid])
