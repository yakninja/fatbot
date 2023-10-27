import logging
import os
from multiprocessing import Lock
import time
import i18n

from sqlalchemy import func, text, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.functions import concat, current_date
from telegram.ext import ContextTypes

from db import db_engine
from models import DailyReport, FutureMessage, date_now
from models.core import daily_report_message

logger = logging.getLogger(__name__)
daily_report_mutex = Lock()


async def daily_report_job(context: ContextTypes.DEFAULT_TYPE = None, db_session=None):
    """
    Select users for daily reporting, queue reports for them
    :param context: optional, not used ATM
    :return:
    """
    if db_session is None:
        db_session = sessionmaker(bind=db_engine)()
    today_date = date_now()

    with daily_report_mutex:
        records = db_session.query(DailyReport) \
            .filter(DailyReport.last_report_date < today_date) \
            .order_by(DailyReport.last_report_date) \
            .limit(10) \
            .all()

        for r in records:
            r.last_report_date = today_date
            db_session.add(r)

        db_session.commit()

    for r in records:
        logger.info(r)
        message = daily_report_message(db_session, r.user, today_date)
        if message:
            fm = FutureMessage(
                user_id=r.user_id,
                created_at=func.now(),
                locked_until=func.now(),
                expires_at=text('date_add(now(), interval 1 day)'),
                send_at='{} 07:00:00'.format(
                    today_date),  # todo: user's timezone
                message=message
            )
            db_session.add(fm)
            db_session.commit()
