import i18n
from telegram import Update
from telegram.ext import CallbackContext
from datetime import datetime

from models.food_log import FoodLog, date_now
from db import db_session
from models.food_name import FoodName
from models.unit_name import UnitName
from models.user import get_or_create_user


def settings_command(update: Update, _: CallbackContext) -> None:
    user = get_or_create_user(update.message.from_user.id)
    profile = user.profile
    strings = [
        i18n.t('Daily goal:'),
        '{}\t{}\t{}\t{}'.format(
            i18n.t('Calories'),
            i18n.t('Fat'),
            i18n.t('Carbs'),
            i18n.t('Protein')), '{:.0f}\t{:.0f}\t{:.0f}\t{:.0f}'.format(
            profile.daily_calories,
            profile.daily_fat,
            profile.daily_carbs,
            profile.daily_protein),
    ]
    update.message.reply_text("\n".join(strings))
