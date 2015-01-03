from sqlalchemy import Table, Column, String, Integer

from modules.persistence import Base, getModelBase


"""
Specify custom database tables for your plugins by creating classes here that
subclass Base and the custom ModelBase and include sqlalchemy fields. See the
sqlalchemy docs about declarative schema for more info.

This creates a table in the database called example_thing with two columns, a 50
character string call name and an integer called count.

Importing Thing in the plugin allows manipulating the database using
standard sqlalchemy. See the sqlalchemy persistence module and the sqlalchemy
docs for more info.
"""

ModelBase = getModelBase('example')
class Thing(Base, ModelBase):
    name = Column(String(50))
    count = Column(Integer)
