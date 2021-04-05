import time

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from db import db_session
from models import Base
from models.user_profile import UserProfile


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer(), primary_key=True, unique=True, nullable=False)
    telegram_id = Column(Integer(), unique=True, nullable=False)
    created_at = Column(Integer(), default=time.time, nullable=False)
    updated_at = Column(Integer(), default=time.time, nullable=False)

    profile = relationship('UserProfile', uselist=False, primaryjoin="User.id == UserProfile.user_id")

    def __repr__(self):
        return "<User(id={} telegram_id={})>".format(self.id, self.telegram_id)


def get_or_create_user(telegram_id) -> User:
    user = db_session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id)
        db_session.add(user)
        db_session.commit()
        # TODO: configure calories etc. See https://www.calculator.net/macro-calculator.html
        profile = UserProfile(user_id=user.id,
                              daily_calories=1538,
                              daily_carbs=205,
                              daily_fat=44,
                              daily_protein=94)
        db_session.add(profile)
        db_session.commit()
    return user
