import logging
import os
import i18n

from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, \
    filters, ChatMemberHandler, ChatJoinRequestHandler, Application, JobQueue
from telegram import ChatMember, ChatMemberUpdated, ForceReply, Update, Bot, User as TelegramUser, \
    Message as TelegramMessage
from telegram.constants import ParseMode, ChatAction

from dotenv import load_dotenv

from commands import *
from commands.router import router_command

from jobs import future_message_job, daily_report_job

logger = logging.getLogger(__name__)

i18n.load_path.append('./translations')
i18n.set('filename_format', '{locale}.{format}')
i18n.set('skip_locale_root_data', True)
i18n.set('locale', 'ru')
i18n.set('fallback', 'en')

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OWNER_TELEGRAM_ID = os.getenv('OWNER_TELEGRAM_ID')


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Greet the user on /start"""
    await update.message.reply_text(i18n.t('Hi!'))

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)


def main() -> None:

    application = ApplicationBuilder().token(token=TELEGRAM_TOKEN).build()

    # commands

    application.add_handler(CommandHandler(["start"], start_command))
    application.add_handler(CommandHandler(["settings"], settings_command))
    application.add_handler(CommandHandler(["help"], help_command))
    application.add_handler(CommandHandler(["today"], today_command))
    application.add_handler(CommandHandler(["weight"], weight_entry_command))
    application.add_handler(CommandHandler(["cancel"], cancel_command))

    # admin commands
    application.add_handler(CommandHandler("add_food", add_food_command))
    application.add_handler(CommandHandler("update_food", add_food_command))
    application.add_handler(CommandHandler("add_unit", add_unit_command))
    application.add_handler(CommandHandler("define_unit", define_unit_command))

    # default command: router
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, router_command))

    # jobs
    for i in range(0, int(os.getenv('FUTURE_MESSAGE_JOBS'))):
        application.job_queue.run_repeating(future_message_job, interval=10, first=0)

    application.job_queue.run_repeating(daily_report_job, interval=60, first=0)

    # start the bot

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
