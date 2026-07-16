import logging
import os
import re
import time
from datetime import datetime, timedelta

import i18n
from sqlalchemy import desc, asc
from sqlalchemy.orm import sessionmaker, Session
from telegram import Update
from telegram.ext import ContextTypes

import pandas as pd

from db import db_engine
from models import DateLabel, User, WeightLog, CommandLog
from models.core import get_or_create_user
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


def create_user_weight_chart(db_session: Session, user: User, current_time: datetime = None) -> str:
    current_time = current_time or datetime.now()
    current_timestamp = int(current_time.timestamp())
    one_year_ago = current_timestamp - 86400 * 365

    query = db_session.query(WeightLog.created_at, WeightLog.weight).filter(
        WeightLog.user_id == user.id,
        WeightLog.created_at >= one_year_ago,
    ).order_by(asc('created_at'))

    df = pd.read_sql(query.statement, query.session.bind)
    if df.empty:
        return None

    df['created_at'] = pd.to_datetime(df['created_at'], unit='s')
    one_year_ago_date = (current_time - timedelta(days=365)).date()
    date_labels = db_session.query(DateLabel.label_date, DateLabel.label).filter(
        DateLabel.user_id == user.id,
        DateLabel.label_date >= one_year_ago_date,
        DateLabel.label_date <= current_time.date(),
    ).order_by(DateLabel.label_date).all()

    fig = create_weight_chart_figure(get_weight_chart_ranges(df, current_time), date_labels)
    if not fig:
        return None

    plot_filename = get_temp_filename('png')
    fig.savefig(plot_filename)
    close_weight_chart_figure(fig)
    return plot_filename


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

    replies = {
        user_tid: {'message': message},
        owner_tid: {'message': message}
    }

    plot_filename = create_user_weight_chart(db_session, user)
    if plot_filename:
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
