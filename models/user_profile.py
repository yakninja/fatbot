import re
import time
from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates, relationship, backref

from models import Base


class UserProfile(Base):
    __tablename__ = 'user_profile'

    id = Column(Integer(), primary_key=True, unique=True, nullable=False)
    user_id = Column(Integer(), ForeignKey('user.id'), nullable=False)
    daily_calories = Column(Float(), default=0, nullable=False)
    daily_fat = Column(Float(), default=0, nullable=False)
    daily_carbs = Column(Float(), default=0, nullable=False)
    daily_protein = Column(Float(), default=0, nullable=False)

    def __repr__(self):
        return "<UserProfile(user_id={})>".format(self.user_id)

