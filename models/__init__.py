from datetime import datetime
import time

from pytz import timezone
from sqlalchemy import MetaData, Date, ForeignKey, Boolean, Column, Integer, Float, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base(metadata=MetaData())
UTC = timezone('UTC')


def date_now():
    return datetime.now(UTC).strftime('%Y-%m-%d')


class Food(Base):
    __tablename__ = 'food'

    id = Column(Integer(), primary_key=True, unique=True, nullable=False)
    created_at = Column(Integer(), default=time.time, nullable=False)
    updated_at = Column(Integer(), default=time.time, nullable=False)
    # calories etc are per 1 gram
    calories = Column(Float(), default=0, nullable=False)
    fat = Column(Float(), default=0, nullable=False)
    carbs = Column(Float(), default=0, nullable=False)
    protein = Column(Float(), default=0, nullable=False)

    def __repr__(self):
        return "<Food(id={})>".format(self.id)


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


class FoodName(Base):
    __tablename__ = 'food_name'

    id = Column(Integer(), primary_key=True, unique=True, nullable=False)
    food_id = Column(Integer(), ForeignKey('food.id'), nullable=False)
    name = Column(String(255), nullable=False)
    language = Column(String(8))

    food = relationship('Food', foreign_keys=food_id)

    def __repr__(self):
        return "<FoodName(id={}, food_id={}, name={})>".format(
            self.id, self.food_id, self.name)


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


class Unit(Base):
    __tablename__ = 'unit'

    id = Column(Integer(), primary_key=True, unique=True, nullable=False)

    def __repr__(self):
        return "<Unit(id={})>".format(self.id)


class UnitName(Base):
    __tablename__ = 'unit_name'

    id = Column(Integer(), primary_key=True, unique=True, nullable=False)
    unit_id = Column(Integer(), ForeignKey('unit.id'), nullable=False)
    name = Column(String(255), nullable=False)
    language = Column(String(8))

    unit = relationship('Unit', foreign_keys=unit_id)

    def __repr__(self):
        return "<UnitName(id={})>".format(self.id)


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer(), primary_key=True, unique=True, nullable=False)
    telegram_id = Column(Integer(), unique=True, nullable=False)
    created_at = Column(Integer(), default=time.time, nullable=False)
    updated_at = Column(Integer(), default=time.time, nullable=False)

    profile = relationship('UserProfile', uselist=False, primaryjoin="User.id == UserProfile.user_id")

    def __repr__(self):
        return "<User(id={} telegram_id={})>".format(self.id, self.telegram_id)


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
