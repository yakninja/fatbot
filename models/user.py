import time

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from models import Base
from models.user_profile import UserProfile

noop = UserProfile


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer(), primary_key=True, unique=True, nullable=False)
    telegram_id = Column(Integer(), unique=True, nullable=False)
    created_at = Column(Integer(), default=time.time, nullable=False)
    updated_at = Column(Integer(), default=time.time, nullable=False)

    profile = relationship('UserProfile', uselist=False, primaryjoin="User.id == UserProfile.user_id")

    def __repr__(self):
        return "<User(id={} telegram_id={})>".format(self.id, self.telegram_id)
