import re
import time
from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates, relationship, backref

from models import Base
from models.food import Food

noop = Food


class FoodName(Base):
    __tablename__ = 'food_name'

    id = Column(Integer(), primary_key=True, unique=True, nullable=False)
    food_id = Column(Integer(), ForeignKey('food.id'), nullable=False)
    name = Column(String(255), nullable=False)
    language = Column(String(8))

    food = relationship('Food', foreign_keys=food_id)

    def __repr__(self):
        return "<FoodName(id={}, food_id={}, name={})>".format(self.id, self.food_id, self.name)
