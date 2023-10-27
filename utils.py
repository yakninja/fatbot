import logging
import os
import uuid

import i18n
from sqlalchemy import func

from models import FoodLog, FoodName, UnitName

OWNER_TELEGRAM_ID = os.getenv('OWNER_TELEGRAM_ID')

logger = logging.getLogger(__name__)

TEMP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')

def get_temp_filename(extension: str) -> str:
    if not os.path.exists(TEMP_PATH):
        # Create the 'temp' directory
        os.makedirs(TEMP_PATH)
    random_filename = str(uuid.uuid4())
    return os.path.join(TEMP_PATH, f"{random_filename}.{extension}")

