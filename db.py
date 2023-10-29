import os
from dotenv import load_dotenv

from sqlalchemy import create_engine

load_dotenv()

def get_db_url():
    return "mysql://%s:%s@%s:%s/%s?charset=utf8mb4" % (
        os.getenv("DB_USER", "fatbot"),
        os.getenv("DB_PASSWORD", "fatbot"),
        os.getenv("DB_HOST", "127.0.0.1"),
        os.getenv("DB_PORT", "3307"), # 3307 for tests, 3306 for prod from .env
        os.getenv("DB_NAME", "fatbot"),
    )


db_engine = create_engine(get_db_url(), pool_size=50, max_overflow=10, pool_recycle=3600)
