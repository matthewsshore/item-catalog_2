from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from catalog_database_setup import Base, CatalogTitles, ListItems, UserList
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

# Open google log in client secrets file
CLIENT_ID = json.loads(
    open('client_secret_catalog.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Udacity Item Catalog"

# connect to the catalogDatabase created in catalog_database_setup.py
engine = create_engine('sqlite:///catalogDatabase.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()



# log in for facebook
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_secrets_catalog.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_secrets_catalog.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.2/me"
    # strip expire tag from access token
    token = result.split("&")[0]
    url = 'https://graph.facebook.com/v2.2/me?%s' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.2/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = 'Welcome'
    return output


# log in for Google
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code, now compatible with Python3
    request.get_data()
    code = request.data.decode('utf-8')

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret_catalog.json', scope='')
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
    # Submit request, parse response - Python3 compatible
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

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
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = login_session['username']

    return output


# User Helper Functions
def createUser(login_session):
    newUser = UserList(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(UserList).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(UserList).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(UserList).filter_by(email=email).one()
        return user.id
    except:
        return None


# Begin html templates
# This is the non-logged in homepage
# If user is already logged in and navigates here they will
# be redirected to the user page
@app.route('/')
@app.route('/home')
def showHome():
    categories = session.query(CatalogTitles).all()
    length = len(categories)
    if length > 0:
        length = length -1
        latestCategory = categories[length]
        if 'username' not in login_session:
            state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
            login_session['state'] = state
            return render_template('home.html', categories=categories, latestCategory=latestCategory, STATE=state)
        else:
            return redirect(url_for('loggedInUser'))
    else:
        if 'username' not in login_session:
            state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
            login_session['state'] = state
            return render_template('firstHTML.html', STATE=state)
        else:
            return render_template('firstLoggedInUser.html')



# Home page when you are logged in
# If you are logged in and the owner, then your categories show up with Edit/Delete links
# If you are logged in but not the owner then these edit/delete links are not available
# This is the difference between public and owned, and you can see in the HTML file
# where these links either show up or do not
@app.route('/user')
def loggedInUser():
    user = session.query(UserList).filter_by(email=login_session['email']).one()
    ownedCategories = session.query(CatalogTitles).filter_by(owner_id=login_session['user_id']).all()
    publicCategories = session.query(CatalogTitles).filter(CatalogTitles.owner_id != login_session['user_id']).all()
    return render_template('loggedUser.html', ownedCategories=ownedCategories, user=user, publicCategories=publicCategories)


#Page to create a new category, no inputs needed
#This page is only available once you are logged in.  If you are not logged in
#the html template that renders does not have the Add Category button available
#Therefore the new category page checks login status
@app.route('/newCategory', methods=['GET', 'POST'])
def addNewCategory():
    if 'user_id' not in login_session:
        flash('Please log in to access that page!')
        return redirect(url_for('showHome'))
    if request.method == 'POST':
        user = session.query(UserList).filter_by()
        newCategory = CatalogTitles(
            title=request.form['title'], owner_id=login_session['user_id'], owner_name=login_session['username'])
        session.add(newCategory)
        session.commit()
        flash('New %s category Added' % newCategory.title)
        return redirect(url_for('loggedInUser'))
    else:
        return render_template('newCategory.html')


# Delete a category - categoryID passed into route
# Can only be accessed if you are the owner
# Log in status and ownership are checked at the loggedInUser route
# If you are logged in and the owner, then your categories show up with Edit/Delete links
# If you are logged in but not the owner then these edit/delete links are not available
@app.route('/<int:categoryID>/deleteCategory', methods=['GET', 'POST'])
def deleteCategory(categoryID):
    if 'user_id' not in login_session:
        flash('Please log in to access that page!')
        return redirect(url_for('showHome'))
    deletedCategoryItems = session.query(ListItems).filter_by(category_id=categoryID).all()
    count = len(deletedCategoryItems)
    deletedCategory = session.query(CatalogTitles).filter_by(id=categoryID).one()
    x = 0
    if deletedCategory.owner_id == login_session['user_id']:
        if request.method == 'POST':
            while x < count:
                item = deletedCategoryItems[0]
                session.delete(item)
                session.commit()
                x = x + 1
            session.delete(deletedCategory)
            session.commit()
            flash('%s category deleted' % deletedCategory.title)
            return redirect(url_for('loggedInUser'))
        else:
            return render_template('deleteCategory.html', categoryID=categoryID, deletedCategory=deletedCategory)
    else:
        flash('Please log in to access that page!')
        return redirect(url_for('showHome'))


# Edit category - categoryID passed into route
# Can only be accessed if you are the owner
@app.route('/<int:categoryID>/editCategory', methods=['GET', 'POST'])
def editCategory(categoryID):
    editedCategory = session.query(CatalogTitles).filter_by(id=categoryID).one()
    if 'user_id' not in login_session:
        flash('Please log in to access that page!')
        return redirect(url_for('showHome'))
    if editedCategory.owner_id == login_session['user_id']:
        if request.method == 'POST':
            editedCategory.title = request.form['title']
            flash('%s category has been edited' % editedCategory.title)
            return redirect(url_for('loggedInUser'))
        else:
            return render_template('editCategory.html', category=editedCategory)
    else:
        flash('Please log in to access that page!')
        return redirect(url_for('showHome'))


# Not loggedIn category page
@app.route('/<int:categoryID>')
def categoryPage(categoryID):
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    category = session.query(CatalogTitles).filter_by(id=categoryID).one()
    items = session.query(ListItems).filter_by(category_id=categoryID).all()
    return render_template('categoryPage.html', category=category, items=items, STATE=state)


# Signed In Category Page
# If you own category, template rendered has edit and delete function
# If you are not the owner, tempalte rendered has no edit or delete
@app.route('/user/<int:categoryID>')
def loggedinCategoryPage(categoryID):
    category = session.query(CatalogTitles).filter_by(id=categoryID).one()
    items = session.query(ListItems).filter_by(category_id=categoryID).all()
    if category.owner_id == login_session['user_id']:
        return render_template('loggedin_categorypage.html', category=category, items=items)
    return render_template('loggednonOwnercategoryPage.html', category=category, items=items)


# Add Item to category - accessible only if you are logged in
# see loggedinCategoryPage route
@app.route('/<int:categoryID>/addItem', methods=['GET', 'POST'])
def addItem(categoryID):
    if 'user_id' not in login_session:
        flash('Please log in to access that page!')
        return redirect(url_for('showHome'))
    category = session.query(CatalogTitles).filter_by(id=categoryID).one()
    items = session.query(ListItems).filter_by(category_id=categoryID).all()
    if category.owner_id == login_session['user_id']:
        if request.method == 'POST':
            newItem = ListItems(name=request.form['name'],
                description=request.form['description'], picture=request.form['picture'], category_id=categoryID,
                owner_id=login_session['user_id'], owner_name=login_session['username'])
            session.add(newItem)
            session.commit()
            flash('%s item has been added' % newItem.name)
            return redirect(url_for('loggedinCategoryPage', categoryID=categoryID))
        else:
            return render_template('addItem.html', categoryID=categoryID, category=category)
    else:
        flash('Please log in to access that page!')
        return redirect(url_for('loggedinCategoryPage', categoryID = category.id))


# Not logged in item page
@app.route('/<int:categoryID>/<int:itemID>')
def itemPage(itemID, categoryID):
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    item = session.query(ListItems).filter_by(id=itemID).one()
    category = session.query(CatalogTitles).filter_by(id=categoryID).one()
    return render_template('itemPage.html', item=item, category=category, STATE=state)


# Logged in item page
# If you own category, template rendered has edit and delete function for the item
# If you are not the owner, tempalte rendered has no edit or delete
@app.route('/user/<int:categoryID>/<int:itemID>')
def loggedinItemPage(itemID, categoryID):
    item = session.query(ListItems).filter_by(id=itemID).one()
    category = session.query(CatalogTitles).filter_by(id=categoryID).one()
    if item.owner_id == login_session['user_id']:
        return render_template('loggedin_itemPage.html', item=item, category=category)
    else:
        return render_template('loggednonOwnerItemPage.html', item=item, category=category)


# Edit Item - accessible only if you are logged in and the owner
# see loggedinItemPage route
@app.route('/<int:categoryID>/<int:itemID>/editItem', methods=['GET', 'POST'])
def editItem(itemID, categoryID):
    if 'user_id' not in login_session:
        flash('Please log in to access that page!')
        return redirect(url_for('showHome'))
    item = session.query(ListItems).filter_by(id=itemID).one()
    category = session.query(CatalogTitles).filter_by(id=categoryID).one()
    if item.owner_id == login_session['user_id']:
        if request.method == 'POST':
            if request.form['name']:
                item.name = request.form['name']
            if request.form['description']:
                item.description = request.form['description']
            if request.form['picture']:
                item.picture = request.form['picture']
            flash('%s category has been edited' % item.name)
            return redirect(url_for('loggedinItemPage', itemID=item.id, categoryID=category.id))
        else:
            return render_template('editItem.html', item=item, category=category)
    else:
        flash('Please log in to access that page!')
        return redirect(url_for('loggedinItemPage', itemID = item.id, categoryID = category.id))

# Delete Item - accessible only if you are logged in and the owner
# see loggedinItemPage route
@app.route('/<int:categoryID>/<int:itemID>/deleteItem', methods=['GET', 'POST'])
def deleteItem(itemID, categoryID):
    if 'user_id' not in login_session:
        flash('Please log in to access that page!')
        return redirect(url_for('showHome'))
    item = session.query(ListItems).filter_by(id=itemID).one()
    category = session.query(CatalogTitles).filter_by(id=categoryID).one()
    if item.owner_id == login_session['user_id']:
        if request.method == 'POST':
            session.delete(item)
            session.commit()
            flash('%s category deleted' % item.name)
            return redirect(url_for('loggedinCategoryPage', categoryID=item.category_id))
        else:
            return render_template('deleteItem.html', item=item, category=category)
    else:
        flash('Please log in to access that page!')
        return redirect(url_for('loggedinItemPage', itemID = item.id, categoryID = category.id))


# ALL JSON ENDPOINTS ACCESSIBLE WITHOUT LOGGING IN
# Creates JSON for all the categories
@app.route('/category/json')
@app.route('/category/JSON')
def categoryJSON():
    category = session.query(CatalogTitles).all()
    return jsonify(Categories=[i.serialize for i in category])


# Creates JSON for all the items in a category
@app.route('/<int:categoryID>/json')
@app.route('/<int:categoryID>/JSON')
def itemListJSON(categoryID):
    item = session.query(ListItems).filter_by(category_id=categoryID).all()
    return jsonify(Items=[i.serialize for i in item])


# Creates a JSON of just one item in a specific category
@app.route('/<int:categoryID>/<int:itemID>/json')
@app.route('/<int:categoryID>/<int:itemID>/JSON')
def itemJSON(categoryID, itemID):
    item = session.query(ListItems).filter_by(id=itemID).all()
    return jsonify(Items=[i.serialize for i in item])


# this portion checks to see what provider
# was used to log in then disconnects it when logging out
@app.route('/logout')
def logout():
    if login_session['provider'] == "facebook":
        facebook_id = login_session['facebook_id']
        # The access token must me included to successfully logout
        access_token = login_session['access_token']
        url = 'https://graph.facebook.com/%s%s/permissions' % (facebook_id, access_token)
        h = httplib2.Http()
        result = h.request(url, 'DELETE')[1]
        del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        return redirect(url_for('showHome'))
    if login_session['provider'] == "google":
        # Only disconnect a connected user.
        credentials = login_session.get('access_token')
        if credentials is None:
            response = make_response(
                json.dumps('Current user not connected.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response
        access_token = credentials
        url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
        h = httplib2.Http()
        result = h.request(url, 'GET')[0]
        if result['status'] != '200':
            # For whatever reason, the given token was invalid.
            response = make_response(
                json.dumps('Failed to revoke token for given user. %s' % access_token))
            response.headers['Content-Type'] = 'application/json'
            return response
        if result['status'] == '200':
            del login_session['access_token']
            del login_session['username']
            del login_session['email']
            del login_session['picture']
            del login_session['gplus_id']
            return redirect(url_for('showHome'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
