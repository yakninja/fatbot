import time

from sqlalchemy import Column, Integer, Float, String, ForeignKey
from sqlalchemy.orm import relationship

from models import Base
from models.unit import Unit

noop = Unit


class UnitName(Base):
    __tablename__ = 'unit_name'

    id = Column(Integer(), primary_key=True, unique=True, nullable=False)
    unit_id = Column(Integer(), ForeignKey('unit.id'), nullable=False)
    name = Column(String(255), nullable=False)
    language = Column(String(8))

    unit = relationship('Unit', foreign_keys=unit_id)

    def __repr__(self):
        return "<UnitName(id={})>".format(self.id)
