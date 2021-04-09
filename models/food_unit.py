import time

from sqlalchemy import Column, Integer, Float, String

from models import Base


class FoodUnit(Base):
    __tablename__ = 'food_unit'

    id = Column(Integer(), primary_key=True, unique=True, nullable=False)

    def __repr__(self):
        return "<FoodUnit(id={})>".format(self.id)
