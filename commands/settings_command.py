import i18n
from sqlalchemy.orm import sessionmaker
from telegram import Update
from telegram.ext import CallbackContext

from db import db_engine
from models.core import get_or_create_user


def settings_command(update: Update, _: CallbackContext) -> None:
    db_session = sessionmaker(bind=db_engine)()
    user = get_or_create_user(db_session, update.message.from_user.id)
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
