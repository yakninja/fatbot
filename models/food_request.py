import re
import time
from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates, relationship, backref

from models import Base
from models.user import User

noop = User


class FoodRequest(Base):
    __tablename__ = 'food_request'

    id = Column(Integer(), primary_key=True, unique=True, nullable=False)
    user_id = Column(Integer(), ForeignKey('user.id'), nullable=False)
    created_at = Column(Integer(), default=time.time, nullable=False)
    qty = Column(Float(), nullable=False)
    request = Column(String(255), nullable=False)

    user = relationship('User', foreign_keys=user_id)

    def __repr__(self):
        return "<FoodRequest(user_id={}, request={})>".format(self.user_id, self.request)
