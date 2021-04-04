import time

from sqlalchemy import Column, Integer, Float

from models import Base


class Food(Base):
    __tablename__ = 'food'

    id = Column(Integer(), primary_key=True, unique=True, nullable=False)
    created_at = Column(Integer(), default=time.time, nullable=False)
    updated_at = Column(Integer(), default=time.time, nullable=False)
    calories = Column(Float(), default=0, nullable=False)
    fat = Column(Float(), default=0, nullable=False)
    carbs = Column(Float(), default=0, nullable=False)
    protein = Column(Float(), default=0, nullable=False)

    def __repr__(self):
        return "<Food(id={})>".format(self.id)
