import logging
import os
import re
import time
from datetime import datetime, timedelta

import i18n
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
    one_month_ago = current_timestamp - 86400 * 30
    one_year_ago = current_timestamp - 86400 * 365
    query = db_session.query(WeightLog.created_at, WeightLog.weight).filter(
        and_(
            WeightLog.user_id == user.id,
            or_(WeightLog.created_at >= one_month_ago,
                WeightLog.created_at >= one_year_ago)
        )
    ).order_by(asc('created_at'))

    # Convert the query result to a DataFrame
    df = pd.read_sql(query.statement, query.session.bind)

    # Convert Unix timestamps to datetime objects for plotting
    df['created_at'] = pd.to_datetime(df['created_at'], unit='s')

    # Convert Unix timestamps back to datetime objects for filtering
    one_month_ago_datetime = datetime.fromtimestamp(one_month_ago)
    one_year_ago_datetime = datetime.fromtimestamp(one_year_ago)

    # Filter the DataFrame
    df_month = df[df['created_at'] >= one_month_ago_datetime]
    df_year = df[df['created_at'] >= one_year_ago_datetime]

    # Now plot the data

    # Create a figure with size 800x400 pixels
    fig, axes = plt.subplots(2, 1, figsize=(8, 4), dpi=100)

    # Plot weight change over 1 month
    # [left, bottom, width, height]
    axes[0].set_position([0.08, 0.6, 0.9, 0.3])
    # (look into it later)
    if False and len(df_month) > 3:  # Need at least four points for cubic spline
        x = np.array([md.toordinal() for md in df_month['created_at']])
        y = df_month['weight']
        spl = UnivariateSpline(x, y, k=3, s=0)
        xnew = np.linspace(x.min(), x.max(), 800)
        ynew = spl(xnew)
        trend_dates = [datetime.fromordinal(int(i)) for i in xnew]
        axes[0].plot(trend_dates, ynew)
    else:
        axes[0].plot(df_month['created_at'], df_month['weight'])
    axes[0].set_title('Month')
    # Get the minimum and maximum values of the weight data for 1 month
    min_weight_month = df_month['weight'].min()
    max_weight_month = df_month['weight'].max()
    if min_weight_month == max_weight_month:
        # If they are equal, set the y-limits to a fixed range or adjust as needed
        fixed_range = 10.0  # Set a fixed range, you can adjust this value
        axes[0].set_ylim(min_weight_month - fixed_range/2, max_weight_month + fixed_range/2)
    else:
        axes[0].set_ylim([df_month['weight'].min(), df_month['weight'].max()])

    # Simplify x-axis to show only first and last date
    if len(df_month) > 0:
        axes[0].set_xticks([df_month['created_at'].iloc[0],
                           df_month['created_at'].iloc[-1]])

    # Plot weight change over 1 year
    # [left, bottom, width, height]
    axes[1].set_position([0.08, 0.1, 0.9, 0.3])  # Move it lower
    axes[1].plot(df_year['created_at'], df_year['weight'])
    axes[1].set_title('Year')
    # Get the minimum and maximum values of the weight data for 1 year
    min_weight_year = df_year['weight'].min()
    max_weight_year = df_year['weight'].max()

    # Check if the minimum and maximum values are equal
    if min_weight_year == max_weight_year:
        # If they are equal, set the y-limits to a fixed range or adjust as needed
        fixed_range = 10.0  # Set a fixed range, you can adjust this value
        axes[1].set_ylim(min_weight_year - fixed_range/2, max_weight_year + fixed_range/2)
    else:
        # If they are not equal, use the min and max values as originally intended
        axes[1].set_ylim(min_weight_year, max_weight_year)
    # Simplify x-axis to show only first and last date
    if len(df_year) > 0:
        axes[1].set_xticks([df_year['created_at'].iloc[0],
                           df_year['created_at'].iloc[-1]])

    # Adding a trend line for the 1-year data
    if len(df_year) > 1:  # Need at least two points for a trend line
        # Converting datetime to numerical for linear regression
        x = np.array([md.toordinal() for md in df_year['created_at']])
        y = df_year['weight']

        # Calculate coefficients for the linear trend line (y = mx + b)
        m, b = np.polyfit(x, y, 1)

        # Generate y-values based on the linear equation
        trend_line = m * x + b

        # Calculate the trend value (weight change)
        trend_value = trend_line[-1] - trend_line[0]

        # Convert numerical x-values back to datetime for plotting
        trend_dates = [datetime.fromordinal(int(i)) for i in x]

        # Plot the trend line
        trend_color = 'red' if trend_value >= 0 else 'green'
        axes[1].plot(trend_dates, trend_line,
                     linestyle='--', color=trend_color)

        # Annotate the plot with the trend value
        trend_text = f"Trend: {'+' if trend_value >= 0 else ''}{trend_value:.2f}"
        axes[1].text(0.02, 0.95, trend_text, transform=axes[1].transAxes,
                     fontsize=8, verticalalignment='top')

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
