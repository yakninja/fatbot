import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db import get_db_url


@pytest.fixture(scope='module')
def db_credentials():
    os.environ['DB_HOST'] = '127.0.0.1'
    os.environ['DB_PORT'] = '3307'
    os.environ['DB_USER'] = 'fatbot'
    os.environ['DB_PASSWORD'] = 'fatbot'
    os.environ['DB_NAME'] = 'fatbot'


@pytest.fixture(scope='module')
def db_session(db_credentials):
    engine = create_engine(get_db_url())
    session = sessionmaker(bind=engine)()
    yield session

