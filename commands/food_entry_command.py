import logging
import os
import re

import i18n
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import sessionmaker, Session
from telegram import Update
from telegram.ext import CallbackContext

from db import db_engine
from exc import FoodNotFound, UnitNotFound, UnitNotDefined
from models import FoodName, UnitName, FoodRequest, FoodUnit
from models.core import get_or_create_user, log_food, get_food_by_name, food_log_message

logger = logging.getLogger(__name__)

OWNER_USER_ID = os.getenv('OWNER_USER_ID')
FOOD_ENTRY_PATTERN = re.compile('^(.+?)(\\s+([0-9.,]+)(\\s?[^%]+)?)?\\s*$')


def parse_food_entry(entry: str) -> (str, float, str):
    """
    :param entry:
    :return: food_name, qty, unit_name
    """
    m = FOOD_ENTRY_PATTERN.match(entry)
    if not m:
        return None, None, None

    food_name = m.groups()[0].strip()
    if not food_name:
        return None, None, None

    try:
        qty = max(1.0, float(m.groups()[2].strip().replace(',', '.')))
    except (IndexError, AttributeError):
        qty = 1

    try:
        unit_name = m.groups()[3].strip().lower()
    except (IndexError, AttributeError):
        unit_name = None

    food_name = food_name.strip(',.')  # some extra stripping

    return food_name, qty, unit_name


def food_entry(db_session: Session, user_telegram_id: int, input_message: str) -> (str, str):
    """
    :param db_session:
    :param user_telegram_id:
    :param input_message:
    :return:
    """
    food_name, qty, unit_name = parse_food_entry(input_message)
    if food_name is None:
        return i18n.t('I don\'t understand'), None

    user = get_or_create_user(db_session, user_telegram_id)

    try:
        food_log = log_food(db_session, i18n.get('locale'), user, food_name, unit_name, qty)
    except FoodNotFound:
        food_request = FoodRequest(user_id=user.id, request=input_message)
        db_session.add(food_request)
        db_session.commit()
        owner_message = [
            i18n.t('Please add new food (values per 100 g)'),
            '/add_food "{}" calories:0.0 fat:0.0 carbs:0.0 protein:0.0 {}'.format(
                food_name, food_request.id),
        ]
        return i18n.t('The food was not found, forwarding request to the owner'), '\n'.join(owner_message)
    except UnitNotFound:
        food_request = FoodRequest(user_id=user.id, request=input_message)
        db_session.add(food_request)
        db_session.commit()
        owner_message = [
            i18n.t('Please add and define new unit'),
            '/add_unit "{}"'.format(unit_name),
            '/define_unit "{}" "{}" grams:100 {}'.format(
                food_name, unit_name, food_request.id),
        ]
        return i18n.t('The food was not found, forwarding request to the owner'), '\n'.join(owner_message)
    except UnitNotDefined:
        food_request = FoodRequest(user_id=user.id, request=input_message)
        db_session.add(food_request)
        db_session.commit()
        owner_message = [
            i18n.t('Please define unit for this food'),
            '/define_unit "{}" "{}" grams:100 default:true {}'.format(
                food_name, unit_name, food_request.id),
        ]
        return i18n.t('The food was not found, forwarding request to the owner'), '\n'.join(owner_message)

    message_lines = [
        i18n.t('Food added'),
        food_log_message(db_session, food_log),
    ]
    message = '\n'.join(message_lines)
    return message, message


def food_entry_command(update: Update, _: CallbackContext) -> None:
    db_session = sessionmaker(bind=db_engine)()
    from_user = update.message.from_user
    info = "{} {}: {}".format(from_user.id, from_user.username, update.message.text)
    logger.info(info)
    _.bot.send_message(OWNER_USER_ID, info)
    user_message, owner_message = food_entry(db_session, from_user.id, update.message.text)
    _.bot.send_message(OWNER_USER_ID, owner_message)
    _.bot.send_message(from_user.id, user_message)
