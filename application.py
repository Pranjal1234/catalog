import os
from flask import Flask, render_template,url_for,request,redirect,jsonify,g
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Catalog, Item
from flask_httpauth import HTTPBasicAuth
from flask import session as login_session

# Flask tool for auth.
auth = HTTPBasicAuth()

# Flask started up
app = Flask(__name__)

# Connection to the catalog database
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

# Session object for SQLalchemy
DBSession = sessionmaker(bind=engine)
session = DBSession()

#ADD @auth.verify_password decorator here
@auth.verify_password
def verify_password(email_or_token, password):
    user_id = User.verify_auth_token(email_or_token)
    if user_id:
        user = session.query(User).filter_by(id = user_id).one()
    else:
        user = session.query(User).filter_by(email = email_or_token).first()
        if not user or not user.verify_password(password):
            return False
    login_session['email'] = user.email
    login_session['id'] = user.id
    login_session['name'] = user.name
    return True

@app.route('/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({'token': token.decode('ascii')})

@app.route('/newuser', methods = ['POST','GET'])
def new_user():
    if request.method == 'POST':
        email = request.form['email']
        name = request.form['name']
        password = request.form['password']
        if email is None or password is None or name is None:
            print "missing arguments"
            abort(400) 
            
        if session.query(User).filter_by(email = email).first() is not None:
            print "existing user"
            user = session.query(User).filter_by(email=email).first()
            return jsonify({'message':'user already exists'}), 200#, {'Location': url_for('get_user', id = user.id, _external = True)}
            
        user = User(email = email, name=name)
        user.hash_password(password)
        session.add(user)
        session.commit()
        return redirect(url_for('loginPage'))#, {'Location': url_for('get_user', id = user.id, _external = True)}
    else:
        return render_template('newuser.html')

@app.route('/login/', methods = ['POST','GET'])
def loginPage():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email is None or password is None:
            print "missing arguments"
            abort(400)
        if(verify_password(email,password)):
            return redirect(url_for('showCatalog'))
        else:
            return jsonify({'message': 'Incorrect'}), 200
    else:
        return render_template('login.html')

@app.route('/')
@app.route('/catalog/')
def showCatalog():
    categories = session.query(Catalog).all()
    latestitems = session.query(Item).order_by('id')
    if 'email' not in login_session:
        return render_template('publiccatalog.html',categories=categories,latestitems=latestitems,session=login_session)
    else:
        return render_template('catalog.html',categories=categories,latestitems=latestitems,session=login_session)

def disconnect():
    if 'email' in login_session:
        del login_session['email']
        del login_session['id']
        del login_session['name']
        print "You have successfully been logged out."
        return redirect(url_for('showCatalog'))
    else:
        print "You were not logged in to a profile"
        return redirect(url_for('showCatalog'))


@app.route('/category/<string:category_name>/')
def showCategory(category_name):
    categories = session.query(Catalog).all()
    category = session.query(Catalog).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category_id=category.id).all()
    cnt = session.query(Item).filter_by(category_id=category.id).count()
    if 'email' not in login_session:
        return render_template('publiccategory.html', categories=categories, category=category,items=items,cnt=cnt)
    else:
        return render_template('category.html', categories=categories, category=category,items=items,cnt=cnt,session=login_session)

    
@app.route('/category/newitem', methods=['GET','POST'])
def newItem():
    if 'email' not in login_session:
        return redirect('/login/')
    if request.method == 'POST':
        category = session.query(Catalog).filter_by(name=request.form['category']).one()
        if category:
            newItem = Item(name=request.form['name'],
                description=request.form['description'],
                category_id=category.id,
                user_id=login_session['id'])
            session.add(newItem)
            session.commit()
        else:
            newCategory = Catalog(name=request.form['category'],
                user_id=login_session['id'])
            session.add(newCategory)
            session.commit()
            category = session.query(Catalog).filter_by(name=request.form['category']).one()
            newItem = Item(name=request.form['name'],
                description=request.form['description'],
                category_id=category.id,
                user_id=login_session['id'])
            session.add(newItem)
            session.commit() 
        return redirect(url_for('showCatalog'))
    else:
        return render_template('newitem.html')

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
