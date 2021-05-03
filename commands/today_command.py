from datetime import datetime

import i18n
from sqlalchemy.orm import sessionmaker
from telegram import Update
from telegram.ext import CallbackContext

from db import db_engine
from models import date_now, FoodLog
from models.core import get_or_create_user, get_food_name, get_unit_name


def today_command(update: Update, _: CallbackContext) -> None:
    db_session = sessionmaker(bind=db_engine)()
    strings = []
    user = get_or_create_user(db_session, update.message.from_user.id)
    profile = user.profile
    food_logs = db_session.query(FoodLog) \
        .filter_by(user_id=user.id, date=date_now()) \
        .order_by(FoodLog.created_at) \
        .all()
    if len(food_logs) == 0:
        strings.append(i18n.t('No entries today'))
    else:
        strings.append('{}\t{}\t{}\t{}\t{}\t{}'.format(
            i18n.t('Time'),
            i18n.t('Food name'),
            i18n.t('Calories'),
            i18n.t('Fat'),
            i18n.t('Carbs'),
            i18n.t('Protein')))

    calories_left = profile.daily_calories
    fat_left = profile.daily_fat
    carbs_left = profile.daily_carbs
    protein_left = profile.daily_protein
    for fl in food_logs:
        food = fl.food
        food_name = get_food_name(db_session, food)
        unit_name = get_unit_name(db_session, fl.unit)
        strings.append('{}\t{} {:.1f} {}\t{:.0f}\t{:.2f}\t{:.2f}\t{:.2f}'.format(
            datetime.utcfromtimestamp(fl.created_at).strftime('%H:%M'),
            food_name,
            fl.qty,
            unit_name,
            fl.calories,
            fl.fat,
            fl.carbs,
            fl.protein))
        calories_left -= fl.calories
        fat_left -= fl.fat
        carbs_left -= fl.carbs
        protein_left -= fl.protein

    strings.append('')

    strings.append(i18n.t('Daily remainder:'))
    strings.append('{}\t{}\t{}\t{}'.format(
        i18n.t('Calories'),
        i18n.t('Fat'),
        i18n.t('Carbs'),
        i18n.t('Protein')))
    strings.append('{:.0f}\t{:.2f}\t{:.2f}\t{:.2f}'.format(
        calories_left,
        fat_left,
        carbs_left,
        protein_left))
    update.message.reply_text("\n".join(strings))
