import logging
import os
import re
from typing import Tuple

import i18n
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import sessionmaker, Session
from telegram import Update
from telegram.ext import CallbackContext

from db import db_engine
from exc import FoodNotFound, UnitNotFound, UnitNotDefined
from models import FoodRequest, User, CommandLog
from models.core import get_or_create_user, log_food, food_log_message, get_unit_by_name

logger = logging.getLogger(__name__)

FOOD_ENTRY_PATTERN = re.compile('^(.+?)(\\s+([0-9.,/]+)(\\s?[^%]+)?)?\\s*$')


def parse_food_entry_message(message: str) -> tuple([str, float, str]):
    """
    :param message:
    :return: food_name, qty, unit_name
    """
    m = FOOD_ENTRY_PATTERN.match(message)
    if not m:
        return None, None, None

    food_name = m.groups()[0].strip()
    if not food_name:
        return None, None, None

    try:
        qty = m.groups()[2].strip().replace(',', '.')
        if '/' in qty:
            parts = qty.split('/')
            if len(parts) == 2 and int(parts[1]) > 0:
                qty = int(parts[0]) / int(parts[1])
        qty = float(qty)
        if qty <= 0:
            qty = 1
    except (IndexError, AttributeError):
        qty = 1

    try:
        unit_name = m.groups()[3].strip().lower()
    except (IndexError, AttributeError):
        unit_name = None

    food_name = food_name.strip(',.')  # some extra stripping

    return food_name, qty, unit_name


def food_entry(db_session: Session, user: User, input_message: str) -> dict:
    """
    :param db_session:
    :param user:
    :param input_message:
    :return: dictionary {telegram_id: message}
    """
    user_tid = str(user.telegram_id)
    owner_tid = os.getenv('OWNER_TELEGRAM_ID')
    food_name, qty, unit_name = parse_food_entry_message(input_message)
    if food_name is None:
        return {user_tid: i18n.t('I don\'t understand')}

    try:
        food_log = log_food(db_session, i18n.get('locale'), user, food_name, unit_name, qty)
    except FoodNotFound:
        food_request = FoodRequest(user_id=user.id, request=input_message)
        db_session.add(food_request)
        db_session.commit()
        owner_message = [
            i18n.t('Please add new food (values per 100 g)'),
            '/add_food "{}" --calories=0.0 --fat=0.0 --carbs=0.0 --protein=0.0 --request={}'.format(
                food_name, food_request.id),
        ]
        try:
            get_unit_by_name(db_session, i18n.get('locale'), unit_name)
        except NoResultFound:
            owner_message.extend([
                i18n.t('or (if default unit is different from grams)'),
                '/add_food "{}" --calories=0.0 --fat=0.0 --carbs=0.0 --protein=0.0'.format(food_name),
                '/add_unit "{}"'.format(unit_name),
                '/define_unit "{}" "{}" --grams=100 --default=true --request={}'.format(
                    food_name, unit_name, food_request.id),
            ])

        return {
            user_tid: i18n.t('The food was not found, forwarding request to the owner'),
            owner_tid: '\n'.join(owner_message),
        }
    except UnitNotFound:
        food_request = FoodRequest(user_id=user.id, request=input_message)
        db_session.add(food_request)
        db_session.commit()
        owner_message = [
            i18n.t('Please add and define new unit'),
            '/add_unit "{}"'.format(unit_name),
            '/define_unit "{}" "{}" --grams=100 --request={}'.format(
                food_name, unit_name, food_request.id),
        ]
        return {
            user_tid: i18n.t('The food was not found, forwarding request to the owner'),
            owner_tid: '\n'.join(owner_message),
        }
    except UnitNotDefined:
        food_request = FoodRequest(user_id=user.id, request=input_message)
        db_session.add(food_request)
        db_session.commit()
        owner_message = [
            i18n.t('Please define unit for this food'),
            '/define_unit "{}" "{}" --grams=100 --default=true --request={}'.format(
                food_name, unit_name, food_request.id),
        ]
        return {
            user_tid: i18n.t('The food was not found, forwarding request to the owner'),
            owner_tid: '\n'.join(owner_message),
        }

    command_log = CommandLog(user_id=user.id, command_type=CommandLog.FOOD_ENTRY,
                             command=input_message)
    db_session.add(command_log)
    db_session.commit()

    message_lines = [
        i18n.t('Food added'),
        food_log_message(db_session, food_log),
    ]
    message = '\n'.join(message_lines)
    return {
        user_tid: message,
        owner_tid: message,
    }


def food_entry_command(update: Update, _: CallbackContext) -> None:
    """
    Process food entry, echo it to the owner for debugging
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
    if user is None:
        logger.info("User not found, new users disabled?")
        return
    messages = food_entry(db_session, user, update.message.text)
    for tid in messages.keys():
        _.bot.send_message(tid, messages[tid])
