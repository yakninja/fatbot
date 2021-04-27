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
from models.core import log_food, get_food_by_name, create_food
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


def add_food(db_session: Session, user: User, input_message: str) -> (str, str):
    """
    :param db_session:
    :param user:
    :param input_message:
    :return: user_message, owner_message
    """
    try:
        params = parse_add_food_message(input_message)
    except ValueError:
        return i18n.t('Invalid command format'), None

    if str(user.telegram_id) != str(os.getenv('OWNER_USER_ID')):
        return i18n.t('Invalid user id'), None

    try:
        get_food_by_name(db_session, i18n.get('locale'), params['food_name'])
        return i18n.t('Food already exists'), None
    except NoResultFound:
        pass

    request_id = params['request']
    del (params['request'])
    create_food(db_session, locale=i18n.get('locale'), **params)
    if request_id:
        request = db_session.query(FoodRequest).get(request_id)
        if request:
            # now when food is added, repeat the request
            user_message, owner_message = food_entry(db_session, user, request.request)
    return i18n.t('Food added'), None


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
