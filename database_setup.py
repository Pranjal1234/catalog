import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
	__tablename__='user'
	id = Column(Integer, primary_key=True)
	name = Column(String(250), nullable=False, unique=True)
	email = Column(String(250), nullable=False)

class Catalog(Base):
	__tablename__='catalog'
	name = Column(String(80), nullable = False)
	id = Column(Integer, primary_key = True)

class Item(Base):
	__tablename__='item'
	name = Column(String(80), nullable = False)
	id = Column(Integer, primary_key = True)
	description = Column(String(280))
	category_id = Column(Integer, ForeignKey('category.id'))
	category = relationship(Catalog)

engine = create_engine('sqlite:///catalog.db')

Base.metadata.create_all(engine)