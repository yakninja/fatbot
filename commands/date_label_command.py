import logging
import os
import re
import time
from datetime import datetime

import i18n
from sqlalchemy.orm import Session, sessionmaker
from telegram import Update
from telegram.ext import ContextTypes

from commands.weight_entry_command import create_user_weight_chart
from db import db_engine
from models import DateLabel, User
from models.core import get_or_create_user

logger = logging.getLogger(__name__)

DATE_FORMAT = '%Y-%m-%d'
MAX_LABEL_LENGTH = 32


def get_add_date_label_pattern():
    return re.compile(
        '^/(label|date_label|add_label|add_date_label)'
        '\\s+(\\d{4}-\\d{2}-\\d{2})\\s+(.+)$',
        re.I,
    )


def get_remove_date_label_pattern():
    return re.compile(
        '^/(unlabel|remove_label|remove_date_label|delete_label)'
        '\\s+(\\d{4}-\\d{2}-\\d{2})\\s*$',
        re.I,
    )


def get_date_label_pattern():
    return re.compile(
        '^/(label|date_label|add_label|add_date_label|unlabel|remove_label|remove_date_label|delete_label)\\b',
        re.I,
    )


def parse_label_date(date_string):
    return datetime.strptime(date_string, DATE_FORMAT).date()


def date_label_replies(db_session: Session, user: User, message: str) -> dict:
    user_tid = str(user.telegram_id)
    owner_tid = os.getenv('OWNER_TELEGRAM_ID')
    replies = {
        user_tid: {'message': message},
        owner_tid: {'message': message},
    }

    plot_filename = create_user_weight_chart(db_session, user)
    if plot_filename:
        replies[user_tid]['plot_file'] = plot_filename
        replies[owner_tid]['plot_file'] = plot_filename

    return replies


def add_date_label(db_session: Session, user: User, date_string: str, label: str) -> dict:
    try:
        label_date = parse_label_date(date_string)
    except ValueError:
        return {str(user.telegram_id): {'message': i18n.t('I don\'t understand')}}

    label = label.strip()
    if not label or len(label) > MAX_LABEL_LENGTH:
        return {
            str(user.telegram_id): {
                'message': i18n.t(
                    'Date label must be %{count} characters or fewer',
                    count=MAX_LABEL_LENGTH,
                )
            }
        }

    date_label = db_session.query(DateLabel).filter_by(
        user_id=user.id,
        label_date=label_date,
    ).first()
    if not date_label:
        date_label = DateLabel(user_id=user.id, label_date=label_date)

    date_label.label = label
    date_label.updated_at = time.time()
    db_session.add(date_label)
    db_session.commit()

    message = i18n.t(
        'Date label saved: %{date} %{label}',
        date=label_date.strftime(DATE_FORMAT),
        label=label,
    )
    return date_label_replies(db_session, user, message)


def remove_date_label(db_session: Session, user: User, date_string: str) -> dict:
    try:
        label_date = parse_label_date(date_string)
    except ValueError:
        return {str(user.telegram_id): {'message': i18n.t('I don\'t understand')}}

    date_label = db_session.query(DateLabel).filter_by(
        user_id=user.id,
        label_date=label_date,
    ).first()

    if not date_label:
        message = i18n.t(
            'No date label found for %{date}',
            date=label_date.strftime(DATE_FORMAT),
        )
        return date_label_replies(db_session, user, message)

    label = date_label.label
    db_session.delete(date_label)
    db_session.commit()

    message = i18n.t(
        'Date label removed: %{date} %{label}',
        date=label_date.strftime(DATE_FORMAT),
        label=label,
    )
    return date_label_replies(db_session, user, message)


def date_label(db_session: Session, user: User, input_message: str) -> dict:
    add_match = get_add_date_label_pattern().match(input_message)
    if add_match:
        return add_date_label(db_session, user, add_match.groups()[1], add_match.groups()[2])

    remove_match = get_remove_date_label_pattern().match(input_message)
    if remove_match:
        return remove_date_label(db_session, user, remove_match.groups()[1])

    return {str(user.telegram_id): {'message': i18n.t('I don\'t understand')}}


async def date_label_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db_session = sessionmaker(bind=db_engine)()
    from_user = update.message.from_user
    owner_tid = os.getenv('OWNER_TELEGRAM_ID')

    info = "{} {}: {}".format(from_user.id, from_user.username, update.message.text)
    logger.info(info)
    await context.bot.send_message(owner_tid, info)

    user = get_or_create_user(db_session, from_user.id)
    if user is None:
        return

    messages = date_label(db_session, user, update.message.text)
    for tid in messages.keys():
        await context.bot.send_message(tid, messages[tid]['message'])
        if 'plot_file' in messages[tid]:
            with open(messages[tid]['plot_file'], 'rb') as f:
                await context.bot.send_photo(tid, f)
