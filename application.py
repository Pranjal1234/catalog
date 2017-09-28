import os
from flask import Flask, render_template,url_for,request,redirect,jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Flask started up
app = Flask(__name__)

# Connection to the catalog database
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

# Session object for SQLalchemy
DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
@app.route('/catalog')
def showCatalog():
	pass

@app.route('/catagory/new', methods=['GET','POST'])
def newCatagory():
	pass

@app.route('/catagory/<str:catagory_name>/edit', methods=['GET','POST'])
def editCatagory():
	pass

@app.route('/catagory/<str:catagory_name>/delete', methods=['GET','POST'])
def deleteCatagory():
	pass

@app.route('/catagory/<str:catagory_name>')
def showCatagory():
	pass

@app.route('/catagory/<str:catagory_name>/new', methods=['GET','POST'])
def newItem():
	pass

@app.route('/catagory/<str:catagory_name>/<str:item>/edit', methods=['GET','POST'])
def editItem():
	pass

@app.route('/catagory/<str:catagory_name>/<str:item>/delete', methods=['GET','POST'])
def deleteItem():
	pass