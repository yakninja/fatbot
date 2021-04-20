import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db import get_db_url
from models import User, FoodName, Food, UnitName, Unit, FoodRequest
from models.core import create_default_units


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


@pytest.fixture(scope='function')
def no_users(db_session):
    db_session.query(User).delete()
    db_session.commit()


@pytest.fixture(scope='function')
def no_food(db_session):
    db_session.query(FoodRequest).delete()
    db_session.query(FoodName).delete()
    db_session.query(Food).delete()
    db_session.commit()


@pytest.fixture(scope='function')
def default_units(db_session):
    db_session.query(UnitName).delete()
    db_session.query(Unit).delete()
    db_session.commit()

    gram_unit_id, pc_unit_id = create_default_units(session=db_session)
