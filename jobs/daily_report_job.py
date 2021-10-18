import logging
import os
from multiprocessing import Lock
import time

from sqlalchemy import func, text, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.functions import concat
from telegram.ext import CallbackContext

from db import db_engine
from models import DailyReport, FutureMessage

logger = logging.getLogger(__name__)
daily_report_mutex = Lock()


def daily_report_job(context: CallbackContext):
    """
    Select users for daily reporting, queue reports for them
    :param context:
    :return:
    """
    db_session = sessionmaker(bind=db_engine)()

    with daily_report_mutex:
        records = db_session.query(DailyReport) \
            .filter(DailyReport.last_report_date < func.curdate()) \
            .order_by(DailyReport.last_report_date) \
            .limit(3) \
            .all()

        for m in messages:
            m.locked_until = text('date_add(now(), interval 1 minute)')
            db_session.add(m)

        db_session.commit()

    for m in messages:
        logger.info(m.message)
        context.bot.send_message(chat_id=m.user.telegram_id, text=m.message)
        db_session.delete(m)
        db_session.commit()
