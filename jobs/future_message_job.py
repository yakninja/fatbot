import logging
from multiprocessing import Lock

from sqlalchemy import func, text, and_
from sqlalchemy.orm import sessionmaker
from telegram.ext import ContextTypes

from db import db_engine
from models import FutureMessage

logger = logging.getLogger(__name__)
future_message_mutex = Lock()


async def future_message_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Select all message queued for sending, send them
    :param context:
    :return:
    """
    db_session = sessionmaker(bind=db_engine)()

    with future_message_mutex:
        """
        Lock messages atomically so other threads won't engage these
        """
        db_session.execute(text('DELETE FROM future_message WHERE expires_at < now()'))
        db_session.commit()

        messages = db_session.query(FutureMessage) \
            .filter(FutureMessage.send_at <= func.now(), FutureMessage.locked_until <= func.now()) \
            .order_by(FutureMessage.created_at) \
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
