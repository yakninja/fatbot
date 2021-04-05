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

    for fl in food_logs:
        food = fl.food
        food_name = db_session.query(FoodName).filter_by(food_id=food.id).first()
        name = food_name.name if food_name else '?'
        strings.append('{}\t{}\t{}\t{}\t{}\t{}'.format(
            datetime.utcfromtimestamp(fl.created_at).strftime('%H:%M'),
            name,
            fl.calories,
            fl.fat,
            fl.carbs,
            fl.protein))

    strings.append('')
    update.message.reply_text("\n".join(strings))
