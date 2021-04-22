import logging
import os

import i18n
from sqlalchemy import func

from models import FoodLog, FoodName, UnitName

OWNER_USER_ID = os.getenv('OWNER_USER_ID')

logger = logging.getLogger(__name__)

