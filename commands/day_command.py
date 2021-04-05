import i18n
from telegram import Update
from telegram.ext import CallbackContext
from datetime import datetime

from models.food_log import FoodLog, date_now
from db import db_session
from models.food_name import FoodName
from models.user import get_or_create_user


def day_command(update: Update, _: CallbackContext) -> None:
    strings = []
    user = get_or_create_user(update.message.from_user.id)
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
        food_name = db_session.query(FoodName).filter_by(food_id=food.id).first()
        name = food_name.name if food_name else '?'
        strings.append('{}\t{}\t{:.0f}\t{:.2f}\t{:.2f}\t{:.2f}'.format(
            datetime.utcfromtimestamp(fl.created_at).strftime('%H:%M'),
            name,
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
