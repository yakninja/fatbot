import re
import time
from sqlalchemy import Column, Integer, String, ForeignKey, Float, Date
from sqlalchemy.orm import validates, relationship, backref
from pytz import timezone
from datetime import datetime

from db import db_session
from models import Base
from models.food import Food
from models.food_unit import FoodUnit
from models.unit import Unit
from models.user import User

noop = Food, User, Unit
UTC = timezone('UTC')


def date_now():
    return datetime.now(UTC).strftime('%Y-%m-%d')


class FoodLog(Base):
    __tablename__ = 'food_log'

    id = Column(Integer(), primary_key=True, unique=True, nullable=False)
    user_id = Column(Integer(), ForeignKey('user.id'), nullable=False)
    food_id = Column(Integer(), ForeignKey('food.id'), nullable=False)
    unit_id = Column(Integer(), ForeignKey('unit.id'), nullable=False)
    created_at = Column(Integer(), default=time.time, nullable=False)
    date = Column(Date(), nullable=False, default=date_now)
    qty = Column(Float(), nullable=False)
    calories = Column(Float(), nullable=False)
    fat = Column(Float(), nullable=False)
    carbs = Column(Float(), nullable=False)
    protein = Column(Float(), nullable=False)

    user = relationship('User', foreign_keys=user_id)
    food = relationship('Food', foreign_keys=food_id)
    unit = relationship('Unit', foreign_keys=unit_id)

    def __repr__(self):
        return "<FoodLog(user_id={}, food_id={})>".format(self.user_id, self.food_id)


def log_food(user: User, food: Food, unit: Unit, qty: float) -> FoodLog:
    """
    :param user:
    :param food:
    :param unit:
    :param qty:
    :return:
    """
    food_unit = db_session.query(FoodUnit).filter_by(food_id=food.id,
                                                     unit_id=unit.id).first()
    multiplier = qty * food_unit.grams / 100
    food_log = FoodLog(user_id=user.id, food_id=food.id,
                       unit_id=unit.id, qty="{:.2f}".format(qty),
                       calories="{:.2f}".format(food.calories * multiplier),
                       carbs="{:.2f}".format(food.carbs * multiplier),
                       fat="{:.2f}".format(food.fat * multiplier),
                       protein="{:.2f}".format(food.protein * multiplier)
                       )
    db_session.add(food_log)
    db_session.commit()
    return food_log
