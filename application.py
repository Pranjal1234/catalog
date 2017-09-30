import os
from flask import Flask, render_template,url_for,request,redirect,jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Catagory, Item

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
	catagories = session.query(Catalog).all()
	latestitems = session.query(Item).order_by(item.id)
	return render_template('publiccatalog.html')

@app.route('/catalog/new', methods=['GET','POST'])
def newCatagory():
	if request.method == 'POST':
		newCatagory = Category(name=request.form['name'])
		session.add(newCatagory)
		session.commit()
		return redirect(url_for('showCatalog'))
	else:
		return render_template('publicnewcategory.html')

@app.route('/catagory/<str:category_name>/edit', methods=['GET','POST'])
def editCatagory():
	editCatagory = session.query(Catalog).filter_by(name=category_name).one()
	if request.method == 'POST':
		editCatagory.name = request.form['name']
		session.add(editCatagory)
		session.commit()
		return redirect(url_for('showCatalog'))
	else:
		return render_template('editcategory.html',catagory = editCatagory)

@app.route('/catagory/<str:category_name>/delete', methods=['GET','POST'])
def deleteCatagory():
	deleteCatagory = session.query(Catalog).filter_by(name=category_name).one()
	if request.method == 'POST':
		editCatagory.name = request.form['name']
		session.delete(editCatagory)
		session.commit()
		return redirect(url_for('showCatalog'))
	else:
		return render_template('deletecategory.html',catagory = editCatagory)

@app.route('/category/<str:category_name>')
def showCategory():
	catagory = session.query(Catalog).filter_by(name=category_name).one()
	items = session.query(Item).filter_by(category_id=category.id).all()
	return render_template('publiccategory.html', catagory=catagory,items=items)

@app.route('/catagory/<str:category_name>/new', methods=['GET','POST'])
def newItem():
	if request.method == 'POST':
		category = session.query(Catalog).filter_by(name=category).one()
		newCatagory = Category(name=request.form['name'],
				description=request.form['description'],
				category_id=category.id)
		session.add(newCatagory)
		session.commit()
		return redirect(url_for('showCatalog'))
	else:
		return render_template('publicnewcatagory.html')

@app.route('/catagory/<str:catagory_name>/<str:item>/edit', methods=['GET','POST'])
def editItem():
	category = session.query(Catalog).filter_by(name=category).one()
	editItem = session.query(Item).filter_by(name=item,category_id=category.id).one()
	if request.method == 'POST':
        if request.form['name']:
            editItem.name = request.form['name']
        if request.form['description']:
            editItem.description = request.form['description']
        session.add(editItem)
        session.commit()
        return redirect(url_for('showCategory',category_name=category.name))
    else:
    	return render_template('editmenuitem.html',category=category.name,item=editItem.name)

@app.route('/catagory/<str:catagory_name>/<str:item>/delete', methods=['GET','POST'])
def deleteItem():
	category = session.query(Catalog).filter_by(name=category).one()
	editItem = session.query(Item).filter_by(name=item,category_id=category.id).one()
	if request.method == 'POST':
        session.delete(editItem)
        session.commit()
        return redirect(url_for('showCategory',category_name=category.name))
    else:
    	return render_template('deletemenuitem.html',category=category.name,item=editItem.name)

if __name__ == '__main__':
	app.debug = True
	app.run(host = '0.0.0.0', port = 8000)
	