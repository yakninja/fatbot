import logging
import os

import i18n
from sqlalchemy import func

from db import db_session
from models.food_log import FoodLog
from models.food_name import FoodName
from models.unit_name import UnitName

OWNER_USER_ID = os.getenv('OWNER_USER_ID')

logger = logging.getLogger(__name__)


def send_food_log(bot, food_log: FoodLog):
    """
    Send a message to food log user about this food log entry
    :param bot:
    :param food_log:
    :return:
    """
    user_profile = food_log.user.profile
    query = db_session.query(
        FoodLog.date,
        func.sum(FoodLog.calories).label('calories'),
        func.sum(FoodLog.carbs).label('carbs'),
        func.sum(FoodLog.fat).label('fat'),
        func.sum(FoodLog.protein).label('protein')
    ).filter_by(user_id=food_log.user_id, date=food_log.date).first()

    calories_left = "{:.2f}".format(max(0, user_profile.daily_calories - query['calories']))
    fat_left = "{:.2f}".format(max(0, user_profile.daily_fat - query['fat']))
    carbs_left = "{:.2f}".format(max(0, user_profile.daily_carbs - query['carbs']))
    protein_left = "{:.2f}".format(max(0, user_profile.daily_protein - query['protein']))

    food = food_log.food
    fn = db_session.query(FoodName).filter_by(
        food_id=food.id, language=i18n.get('locale')).first()
    food_name = fn.name if fn else '?'
    unit = food_log.unit
    un = db_session.query(UnitName).filter_by(
        unit_id=unit.id, language=i18n.get('locale')).first()
    unit_name = un.name if un else '?'

    lines = [
        i18n.t('Food recorded: %{name} %{qty} %{unit}',
               name=food_name, qty=round(food_log.qty), unit=unit_name),
        i18n.t('Calories: %{calories} / %{calories_left}', calories=food_log.calories, calories_left=calories_left),
        i18n.t('Fat: %{fat} / %{fat_left}', fat=food_log.fat, fat_left=fat_left),
        i18n.t('Carbs: %{carbs} / %{carbs_left}', carbs=food_log.carbs, carbs_left=carbs_left),
        i18n.t('Protein: %{protein} / %{protein_left}', protein=food_log.protein, protein_left=protein_left),
    ]
    message = "\n".join(lines)
    bot.send_message(food_log.user.telegram_id, message)
    bot.send_message(OWNER_USER_ID, message)
    logger.info(message)
