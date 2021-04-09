import time

from sqlalchemy import Column, Integer, Float, String

from models import Base


class Unit(Base):
    __tablename__ = 'unit'

    id = Column(Integer(), primary_key=True, unique=True, nullable=False)

    def __repr__(self):
        return "<Unit(id={})>".format(self.id)
