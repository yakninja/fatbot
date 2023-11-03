import logging
import os
import re
import time
from datetime import datetime, timedelta

import i18n
from matplotlib.axes import Axes
from sqlalchemy import desc, asc, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from telegram import Update
from telegram.ext import ContextTypes

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.interpolate import UnivariateSpline

from db import db_engine
from exc import FoodNotFound, UnitNotFound, UnitNotDefined
from models import FoodRequest, User, WeightLog, CommandLog
from models.core import get_or_create_user, log_food, food_log_message
from utils import get_temp_filename

logger = logging.getLogger(__name__)


def get_weight_entry_pattern():
    """
    This depends on locale
    :return:
    """
    return re.compile('^((/weight|{})\\s+)?([0-9.,]+)$'.format(i18n.t('weight')), re.I)

def plot_data(ax: Axes, df: pd.DataFrame, title: str):
    ax.plot(df['created_at'], df['weight'])
    ax.set_title(title)
    min_weight = df['weight'].min()
    max_weight = df['weight'].max()
    ax.set_ylim([min_weight if min_weight != max_weight else min_weight - 5,
                 max_weight if min_weight != max_weight else max_weight + 5])

    if len(df) > 0:
        ax.set_xticks([df['created_at'].iloc[0], df['created_at'].iloc[-1]])

    if len(df) > 1:
        x = np.array([md.toordinal() for md in df['created_at']])
        y = df['weight']
        m, b = np.polyfit(x, y, 1)
        trend_line = m * x + b
        trend_value = trend_line[-1] - trend_line[0]
        trend_dates = [datetime.fromordinal(int(i)) for i in x]
        trend_color = 'red' if trend_value >= 0 else 'green'
        ax.plot(trend_dates, trend_line, linestyle='--', color=trend_color)
        trend_text = f"Trend: {'+' if trend_value >= 0 else ''}{trend_value:.2f}"
        ax.text(0.02, 0.95, trend_text, transform=ax.transAxes, fontsize=8, verticalalignment='top')


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

    matplotlib.use('Agg') # non-interactive backend

    # Get data for the plot
    current_time = datetime.now()
    current_timestamp = int(current_time.timestamp())
    one_week_ago = current_timestamp - 86400 * 7
    one_month_ago = current_timestamp - 86400 * 30
    one_year_ago = current_timestamp - 86400 * 365
    query = db_session.query(WeightLog.created_at, WeightLog.weight).filter(
        WeightLog.user_id == user.id,
        WeightLog.created_at >= one_year_ago  # Fetch records from one year ago up to the current time
    ).order_by(asc('created_at'))

    # Convert the query result to a DataFrame
    df = pd.read_sql(query.statement, query.session.bind)

    # Convert Unix timestamps to datetime objects for plotting
    df['created_at'] = pd.to_datetime(df['created_at'], unit='s')

    # Convert Unix timestamps back to datetime objects for filtering
    one_week_ago_datetime = datetime.fromtimestamp(one_week_ago)
    one_month_ago_datetime = datetime.fromtimestamp(one_month_ago)
    one_year_ago_datetime = datetime.fromtimestamp(one_year_ago)

    # Filter the DataFrame
    df_week = df[df['created_at'] >= one_week_ago_datetime]
    df_month = df[df['created_at'] >= one_month_ago_datetime]
    df_year = df[df['created_at'] >= one_year_ago_datetime]

    # Create a figure with size 800x600 pixels
    fig, axes = plt.subplots(3, 1, figsize=(8, 6), dpi=100)

    # Plot for week
    plot_data(axes[0], df_week, 'Week')

    # Plot for month
    plot_data(axes[1], df_month, 'Month')

    # Plot for year
    plot_data(axes[2], df_year, 'Year')

    # Adjust subplots
    fig.subplots_adjust(hspace=0.4, left=0.08, right=0.9, top=0.95, bottom=0.05)

    # Save the figure
    plot_filename = get_temp_filename('png')
    fig.savefig(plot_filename)

    return {
        user_tid: {'message': message, 'plot_file': plot_filename},
        owner_tid: {'message': message, 'plot_file': plot_filename}
    }


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
        with open(messages[tid]['plot_file'], 'rb') as f:
            await context.bot.send_photo(tid, f)
