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
from models import FoodRequest, User
from models.core import get_food_by_name, create_food, define_unit_for_food, get_gram_unit, get_or_create_user
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
    if params['command_name'] not in ['/add_food', '/update_food']:
        raise ValueError(i18n.t('Invalid command format'))
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

    food = None
    try:
        food = get_food_by_name(db_session, i18n.get('locale'), params['food_name'])
        if params['command_name'] == '/add_food':
            strings = [
                i18n.t('Food already exists'),
                i18n.t('Use /update_food "{}" --calories={} --fat={} --carbs={} --protein={}'.format(
                    params['food_name'],
                    food.calories * 100, food.fat * 100,
                    food.carbs * 100, food.protein * 100))
            ]
            return {user_tid: "\n".join(strings)}
    except NoResultFound:
        if params['command_name'] == '/update_food':
            return {user_tid: i18n.t('Food not found')}

    if params['command_name'] == '/add_food':
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
    else:
        food.calories = params['calories'] / 100
        food.fat = params['fat'] / 100
        food.carbs = params['carbs'] / 100
        food.protein = params['protein'] / 100
        db_session.add(food)
        db_session.commit()
        return {user_tid: i18n.t('Food updated')}


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
