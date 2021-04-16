import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_db_url():
    return "mysql://%s:%s@%s:%s/%s?charset=utf8mb4" % (
        os.getenv("DB_USER", "fatbot"),
        os.getenv("DB_PASSWORD", "fatbot"),
        os.getenv("DB_HOST", "127.0.0.1"),
        os.getenv("DB_PORT", "3306"),
        os.getenv("DB_NAME", "fatbot"),
    )


db_engine = create_engine(get_db_url())
