import os
from flask import Flask, render_template, url_for, request
from flask import redirect, jsonify, flash
from sqlalchemy import create_engine, desc, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Catalog, Item
from flask_httpauth import HTTPBasicAuth
from flask import session as login_session
import random
import string

# Imports needed to handle the gconnect url for google ID
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

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

# For google login
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

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

# Helper functions


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def createUser(login_session):
    newUser = User(name=login_session['name'], email=login_session['email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already \
                                             connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    login_session['provider'] = 'google'
    response = make_response(json.dumps('Successfully connect user', 200))

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    print data
    login_session['name'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    flash("you are now logged in as %s" % login_session['name'])
    print "done!"
    return output

# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s' % access_token
    print 'User name is: '
    print login_session['name']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % \
    login_session['access_token']
    print url
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['name']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token \
                                             for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


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
        state = ''.join(random.choice(string.ascii_uppercase +
                        string.digits) for x in xrange(32))
        login_session['state'] = state
        return render_template('login.html', STATE=state)


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
    if 'gplus_id' in login_session:
        gdisconnect()
        del login_session['provider']
        flash("You logged out successfully!")
        return redirect(url_for('showCatalog'))
    else:
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
            if (request.form['category'] and request.form['name'] and
               request.form['description']):
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
            if (request.form['category'] and request.form['name'] and
               request.form['description']):
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
    if 'email' not in login_session:
        flash("Please login to access")
        return redirect('/login/')
    category = session.query(Catalog).filter_by(name=category_name).one()
    editItem = session.query(Item).filter_by(
        name=item, category_id=category.id).one()
    if editItem.user_id != login_session['id']:
        flash("You are not the orginal creator of this item")
        return redirect(url_for('showCatalog'))
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
    if 'email' not in login_session:
        flash("Please login to access")
        return redirect('/login/')
    category = session.query(Catalog).filter_by(name=category_name).one()
    editItem = session.query(Item).filter_by(
        name=item, category_id=category.id).one()
    if editItem.user_id != login_session['id']:
        flash("You are not the orginal creator of this item")
        return redirect(url_for('showCatalog'))
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
    app.run(host='0.0.0.0', port=8000)
