import time

from sqlalchemy import Column, Integer, Float, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from models import Base
from models.food import Food
from models.unit import Unit

noop = Food, Unit


class FoodUnit(Base):
    __tablename__ = 'food_unit'

    id = Column(Integer(), primary_key=True, unique=True, nullable=False)
    food_id = Column(Integer(), ForeignKey('food.id'), nullable=False)
    unit_id = Column(Integer(), ForeignKey('unit.id'), nullable=False)
    is_default = Column(Boolean(), nullable=False)
    grams = Column(Float(), nullable=False)

    food = relationship('Food', foreign_keys=food_id)
    unit = relationship('Unit', foreign_keys=unit_id)

    def __repr__(self):
        return "<FoodUnit(id={})>".format(self.id)
