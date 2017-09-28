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
	name = Column(String(250), nullable=False)
	email = Column(String(250), nullable=False)

class Category(Base):
	__tablename__='category'
	name = Column(String(80), nullable = False)
	id = Column(Integer, primary_key = True)

class Item(Base):
	__tablename__='item'
	name = Column(String(80), nullable = False)
	id = Column(Integer, primary_key = True)
	course = Column(String(250))
	description = Column(String(280))
	category_id = Column(Integer, ForeignKey('category.id'))
	category = relationship(Category)

engine = create_engine('sqlite:///catolag.db')

Base.metadata.create_all(engine)