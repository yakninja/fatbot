import logging
import os
from multiprocessing import Lock
import time

from sqlalchemy import func, text, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.functions import concat, current_date
from telegram.ext import CallbackContext

from db import db_engine
from models import DailyReport, FutureMessage, date_now
from models.core import daily_report_message

logger = logging.getLogger(__name__)
daily_report_mutex = Lock()


def daily_report_job(context: CallbackContext):
    """
    Select users for daily reporting, queue reports for them
    :param context:
    :return:
    """
    db_session = sessionmaker(bind=db_engine)()
    current_date = date_now()

    with daily_report_mutex:
        records = db_session.query(DailyReport) \
            .filter(DailyReport.last_report_date < text(current_date)) \
            .order_by(DailyReport.last_report_date) \
            .limit(10) \
            .all()

        for r in records:
            r.last_report_date = text(current_date)
            db_session.add(r)

        db_session.commit()

    for r in records:
        logger.info(r)
        message = daily_report_message(db_session, r.user, current_date)
        if message:
            # todo: queue, do not send right away
            context.bot.send_message(chat_id=r.user.telegram_id, text=message)
