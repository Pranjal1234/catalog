import os
from flask import Flask, render_template,url_for,request,redirect,jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Catalog, Item

# Flask started up
app = Flask(__name__)

# Connection to the catalog database
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

# Session object for SQLalchemy
DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
@app.route('/catalog/')
def showCatalog():
    categories = session.query(Catalog).all()
    latestitems = session.query(Item).order_by('id')
    return render_template('publiccatalog.html',categories=categories,latestitems=latestitems)

@app.route('/catalog/new/', methods=['GET','POST'])
def newCategory():
    if request.method == 'POST':
        newCategory = Catalog(name=request.form['name'])
        session.add(newCategory)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('newcategory.html')

@app.route('/category/<string:category_name>/edit/', methods=['GET','POST'])
def editCategory(category_name):
    editCategory = session.query(Catalog).filter_by(name=category_name).one()
    if request.method == 'POST':
        editCategory.name = request.form['name']
        session.add(editCategory)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('editcategory.html',category = editCategory)

@app.route('/category/<string:category_name>/delete/', methods=['GET','POST'])
def deleteCategory(category_name):
    deleteCategory = session.query(Catalog).filter_by(name=category_name).one()
    if request.method == 'POST':
        editCategory.name = request.form['name']
        session.delete(editCategory)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deletecategory.html',category = editCategory)

@app.route('/category/<string:category_name>/')
def showCategory(category_name):
    categories = session.query(Catalog).all()
    category = session.query(Catalog).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category_id=category.id).all()
    cnt = session.query(Item).filter_by(category_id=category.id).count()
    return render_template('publiccategory.html', categories=categories, category=category,items=items,cnt=cnt)

@app.route('/category/<string:category_name>/new', methods=['GET','POST'])
def newItem(category_name):
    if request.method == 'POST':
        category = session.query(Catalog).filter_by(name=category).one()
        newCategory = Catalog(name=request.form['name'],
                description=request.form['description'],
                category_id=category.id)
        session.add(newCategory)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('newcategory.html')

@app.route('/category/<string:category_name>/<string:item>/edit/', methods=['GET','POST'])
def editItem(category_name,item):
    category = session.query(Catalog).filter_by(name=category_name).one()
    editItem = session.query(Item).filter_by(name=item, category_id=category.id).one()
    if request.method == 'POST':
        if request.form['name']:
            editItem.name = request.form['name']
        if request.form['description']:
            editItem.description = request.form['description']
        session.add(editItem)
        session.commit()
        return redirect(url_for('showCategory',category_name=category.name))
    else:
        return render_template('edititem.html',category=category.name,item=editItem.name)

@app.route('/category/<string:category_name>/<string:item>/delete/', methods=['GET','POST'])
def deleteItem(category_name,item):
    category = session.query(Catalog).filter_by(name=category_name).one()
    editItem = session.query(Item).filter_by(name=item,category_id=category.id).one()
    if request.method == 'POST':
        session.delete(editItem)
        session.commit()
        return redirect(url_for('showCategory',category_name=category.name))
    else:
        return render_template('deleteitem.html',category=category.name,item=editItem.name)

@app.route('/category/<string:category_name>/<string:item>/')
def showItem(category_name,item):
    category = session.query(Catalog).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(category_id=category.id,name=item).one()
    return render_template('publicitem.html', category=category,item=item)

if __name__ == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0', port = 8000)
