import os
from flask import Flask, render_template, url_for, request
from flask import redirect, jsonify, flash
from sqlalchemy import create_engine, desc, asc
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

# ADD @auth.verify_password decorator here


@auth.verify_password
def verify_password(email_or_token, password):
    user_id = User.verify_auth_token(email_or_token)
    if user_id:
        user = session.query(User).filter_by(id=user_id).one()
    else:
        user = session.query(User).filter_by(email=email_or_token).first()
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


@app.route('/catalog/JSON/')
def catalogJSON():
    categories = session.query(Catalog).all()
    catalog = []
    for i in categories:
        items = session.query(Item).filter_by(category_id=i.id).all()
        item = []
        for j in items:
            add = {
                'cat_id': i.id,
                'description': j.description,
                'id': j.id,
                'title': j.name
            }
            item.append(add)
        add = {
            'id': i.id,
            'name': i.name,
            'item': item
        }
        catalog.append(add)
    return jsonify(Category=catalog)


@app.route('/catalog/<string:category_name>/JSON/')
def categoryJSON(category_name):
    category = session.query(Catalog).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category_id=category.id).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/newuser', methods=['POST', 'GET'])
def new_user():
    if request.method == 'POST':
        email = request.form['email']
        name = request.form['name']
        password = request.form['password']
        if email is None or password is None or name is None:
            flash("missing arguments")
            return redirect(url_for('new_user'))

        if session.query(User).filter_by(email=email).first() is not None:
            print "existing user"
            user = session.query(User).filter_by(email=email).first()
            flash('The email provided is already associated with \
                an account please login')
            return redirect(url_for('loginPage'))

        user = User(email=email, name=name)
        user.hash_password(password)
        session.add(user)
        session.commit()
        flash('Successfully created an account')
        return redirect(url_for('loginPage'))
    else:
        return render_template('newuser.html')


@app.route('/login/', methods=['POST', 'GET'])
def loginPage():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email is None or password is None:
            flash("missing arguments")
            return redirect(url_for('loginPage'))
        if(verify_password(email, password)):
            flash("Logged in successfully as %s" % login_session['name'])
            return redirect(url_for('showCatalog'))
        else:
            flash('Incorrect password or email')
            return redirect(url_for('loginPage'))
    else:
        return render_template('login.html')


@app.route('/')
@app.route('/catalog/')
def showCatalog():
    categories = session.query(Catalog).all()
    latestitems = session.query(Item).order_by(Item.id.desc()).limit(5).all()
    if 'email' not in login_session:
        return render_template('publiccatalog.html', categories=categories,
                               latestitems=latestitems, session=login_session)
    else:
        return render_template('catalog.html', categories=categories,
                               latestitems=latestitems, session=login_session)


@app.route('/logout/')
def disconnect():
    if 'email' in login_session:
        del login_session['email']
        del login_session['id']
        del login_session['name']
        print "You have successfully been logged out."
        flash("You logged out successfully!")
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
        return render_template('publiccategory.html', categories=categories,
                               category=category, items=items, cnt=cnt)
    else:
        return render_template('category.html', categories=categories,
                               category=category, items=items, cnt=cnt,
                               session=login_session)


@app.route('/category/newitem', methods=['GET', 'POST'])
def newItem():
    if 'email' not in login_session:
        flash("Please login to access")
        return redirect('/login/')
    if request.method == 'POST':
        if session.query(Catalog.name).filter_by(
                name=request.form['category']).scalar() is not None:
            if request.form['category'] and request.form['name'] and \
            request.form['description']:
                category = session.query(Catalog).filter_by(
                    name=request.form['category']).one()
                newItem = Item(name=request.form['name'],
                               description=request.form['description'],
                               category_id=category.id,
                               user_id=login_session['id'])
                session.add(newItem)
                session.commit()
                flash('New Item Created')
                return redirect(url_for('showCatalog'))
            else:
                flash('Not all the fields were filled!')
                return redirect(url_for('newItem'))
        else:
            if request.form['category'] and request.form['name'] and \
            request.form['description']:
                newCategory = Catalog(name=request.form['category'],
                                      user_id=login_session['id'])
                session.add(newCategory)
                session.commit()
                category = session.query(Catalog).filter_by(
                    name=request.form['category']).one()
                newItem = Item(name=request.form['name'],
                               description=request.form['description'],
                               category_id=category.id,
                               user_id=login_session['id'])
                session.add(newItem)
                session.commit()
                flash('New Category Created')
                flash('New Item Created')
                return redirect(url_for('showCatalog'))
            else:
                flash('Not all the fields were filled!')
                return redirect(url_for('newItem'))
    else:
        return render_template('newitem.html')


@app.route('/category/<string:category_name>/<string:item>/edit/',
           methods=['GET', 'POST'])
def editItem(category_name, item):
    category = session.query(Catalog).filter_by(name=category_name).one()
    editItem = session.query(Item).filter_by(
        name=item, category_id=category.id).one()
    if request.method == 'POST':
        if request.form['name']:
            editItem.name = request.form['name']
        if request.form['description']:
            editItem.description = request.form['description']
        if request.form['category']:
            if session.query(Catalog.name).filter_by(
                    name=request.form['category']).scalar() is not None:
                category = session.query(Catalog).filter_by(
                    name=request.form['category']).one()
                editItem.category_id = category.id
            else:
                newCategory = Catalog(name=category_name,
                                      user_id=login_session['id'])
                session.add(newCategory)
                session.commit()
                category = session.query(Catalog).filter_by(
                    name=request.form['category']).one()
                edititem.category_id = category.id
                flash('New Category Created!')

        editItem.user_id = login_session['id']
        session.add(editItem)
        session.commit()
        flash('Item Edited!')
        return redirect(url_for('showItem', category_name=category.name,
                        item=editItem.name))
    else:
        return render_template('edititem.html', category=category,
                               item=editItem)


@app.route('/category/<string:category_name>/<string:item>/delete/',
           methods=['GET', 'POST'])
def deleteItem(category_name, item):
    category = session.query(Catalog).filter_by(name=category_name).one()
    editItem = session.query(Item).filter_by(
        name=item, category_id=category.id).one()
    if request.method == 'POST':
        session.delete(editItem)
        session.commit()
        flash('Item deleted')
        return redirect(url_for('showCategory', category_name=category.name))
    else:
        return render_template('deleteitem.html', category=category,
                               item=editItem)


@app.route('/category/<string:category_name>/<string:item>/')
def showItem(category_name, item):
    category = session.query(Catalog).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(
        category_id=category.id, name=item).one()
    if 'email' in login_session and login_session['id'] == item.user_id:
        return render_template('item.html', category=category,
                               item=item, session=login_session)
    else:
        return render_template('publicitem.html', category=category,
                               item=item, session=login_session)

# Temporary fix to the css file problem


@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)

if __name__ == '__main__':
    app.debug = True
    app.secret_key = 'super_secret_key'
    app.run(host='0.0.0.0', port=5000)
