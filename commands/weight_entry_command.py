import logging
import os
import re
import time
from datetime import datetime

import i18n
from sqlalchemy import desc, asc, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from telegram import Update
from telegram.ext import ContextTypes

import pandas as pd

from db import db_engine
from exc import FoodNotFound, UnitNotFound, UnitNotDefined
from models import FoodRequest, User, WeightLog, CommandLog
from models.core import get_or_create_user, log_food, food_log_message
from utils import get_temp_filename
from weight_charts import (
    close_weight_chart_figure,
    create_weight_chart_figure,
    get_weight_chart_ranges,
)

logger = logging.getLogger(__name__)


def get_weight_entry_pattern():
    """
    This depends on locale
    :return:
    """
    return re.compile('^((/weight|{})\\s+)?([0-9.,]+)$'.format(i18n.t('weight')), re.I)


def weight_entry(db_session: Session, user: User, input_message: str) -> dict:
    """
    :param db_session:
    :param user:
    :param input_message:
    :return: dictionary {telegram_id: message}
    """
    user_tid = str(user.telegram_id)
    owner_tid = os.getenv('OWNER_TELEGRAM_ID')
    m = get_weight_entry_pattern().match(input_message)
    invalid_reply = {user_tid: {'message': i18n.t('I don\'t understand')}}
    if not m:
        return invalid_reply
    try:
        weight = float(m.groups()[2].strip().replace(',', '.'))
        if weight <= 0:
            return invalid_reply
    except (IndexError, AttributeError):
        return invalid_reply

    latest = db_session.query(WeightLog).filter_by(
        user_id=user.id).order_by(desc('created_at')).first()

    db_session.add(WeightLog(user_id=user.id, weight=weight))
    db_session.commit()

    if latest:
        delta = weight - latest.weight
        days = round(float(time.time() - latest.created_at) / 86400)
        per_day = 0 if days == 0 else delta / days
        delta = '{}{:.1f}'.format('' if delta < 0 else '+', delta)
        per_day = '{}{:.2f}'.format('' if per_day < 0 else '+', per_day)
        message = i18n.t('Weight recorded: %{weight} (%{delta}, %{per_day} per day)',
                         weight='{:.1f}'.format(weight), delta=delta, per_day=per_day)
    else:
        message = i18n.t(
            'Weight recorded: %{weight}', weight='{:.1f}'.format(weight))

    command_log = CommandLog(user_id=user.id, command_type=CommandLog.WEIGHT_ENTRY,
                             command=input_message)
    db_session.add(command_log)
    db_session.commit()

    # Get data for the plot
    current_time = datetime.now()
    current_timestamp = int(current_time.timestamp())
    one_year_ago = current_timestamp - 86400 * 365
    query = db_session.query(WeightLog.created_at, WeightLog.weight).filter(
        WeightLog.user_id == user.id,
        WeightLog.created_at >= one_year_ago  # Fetch records from one year ago up to the current time
    ).order_by(asc('created_at'))

    # Convert the query result to a DataFrame
    df = pd.read_sql(query.statement, query.session.bind)

    # Convert Unix timestamps to datetime objects for plotting
    df['created_at'] = pd.to_datetime(df['created_at'], unit='s')

    fig = create_weight_chart_figure(get_weight_chart_ranges(df, current_time))
    replies = {
        user_tid: {'message': message},
        owner_tid: {'message': message}
    }

    if fig:
        plot_filename = get_temp_filename('png')
        fig.savefig(plot_filename)
        close_weight_chart_figure(fig)
        replies[user_tid]['plot_file'] = plot_filename
        replies[owner_tid]['plot_file'] = plot_filename

    return replies


async def weight_entry_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Process weight entry, echo it to the owner for debugging
    :param update:
    :param _:
    :return:
    """
    db_session = sessionmaker(bind=db_engine)()
    from_user = update.message.from_user
    owner_tid = os.getenv('OWNER_TELEGRAM_ID')

    info = "{} {}: {}".format(
        from_user.id, from_user.username, update.message.text)
    logger.info(info)
    await context.bot.send_message(owner_tid, info)

    user = get_or_create_user(db_session, from_user.id)
    if user is None:
        return
    messages = weight_entry(db_session, user, update.message.text)
    for tid in messages.keys():
        await context.bot.send_message(tid, messages[tid]['message'])
        if 'plot_file' in messages[tid]:
            with open(messages[tid]['plot_file'], 'rb') as f:
                await context.bot.send_photo(tid, f)
