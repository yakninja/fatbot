import re
import time
from sqlalchemy import Column, Integer, String, ForeignKey, Float, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates, relationship, backref
from pytz import timezone
from datetime import datetime

from models import Base
from models.food import Food
from models.user import User

noop = Food, User
UTC = timezone('UTC')


def date_now():
    return datetime.now(UTC).strftime('%Y-%m-%d')


class FoodLog(Base):
    __tablename__ = 'food_log'

    id = Column(Integer(), primary_key=True, unique=True, nullable=False)
    user_id = Column(Integer(), ForeignKey('user.id'), nullable=False)
    food_id = Column(Integer(), ForeignKey('food.id'), nullable=False)
    created_at = Column(Integer(), default=time.time, nullable=False)
    date = Column(Date(), nullable=False, default=date_now)
    qty = Column(Float(), nullable=False)
    calories = Column(Float(), nullable=False)
    fat = Column(Float(), nullable=False)
    carbs = Column(Float(), nullable=False)
    protein = Column(Float(), nullable=False)

    user = relationship('User', foreign_keys=user_id)
    food = relationship('Food', foreign_keys=food_id)

    def __repr__(self):
        return "<FoodLog(user_id={}, food_id={})>".format(self.user_id, self.food_id)


def log_food(user: User, food: Food, qty: float) -> FoodLog:
    """
    Oatmeal 50 = Oatmeal 100 g * (1 (g_per_unit) * 50 / 100)
    Apple 1 = Apple 100 g * (182 (g_per_unit) * 1 / 100)
    :param user:
    :param food:
    :param qty:
    :return:
    """
    multiplier = qty * food.g_per_unit / 100
    food_log = FoodLog(user_id=user.id, food_id=food.id, qty="{:.2f}".format(qty),
                       calories="{:.2f}".format(food.calories * multiplier),
                       carbs="{:.2f}".format(food.carbs * multiplier),
                       fat="{:.2f}".format(food.fat * multiplier),
                       protein="{:.2f}".format(food.protein * multiplier)
                       )
    db_session.add(food_log)
    db_session.commit()
    return food_log