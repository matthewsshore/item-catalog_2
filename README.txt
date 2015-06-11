What is this application:
This is a catalog/blog type application.  Users can view and create their own "Categories"
and in those categories add items and descriptions.  I have seeded the application with several categories 
and items to act as a start.

How does it work:
When not logged in, you can view all the categories on the site, click in and see the items, and then click into items to read their descriptions.

When logged in, you can view the categories you have created as well as those created by others.  If you are the owner of the category/item you can edit and delete them.  You can also add new categories and/or items.

You can only add categories when you are logged in, and you can only edit/delete categories/items when you are the owner.

You can login with either Google or Facebook accounts

Python Modules Imported into catalogProject.py:
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
	from sqlalchemy.ext.declarative import declarative_base
	from sqlalchemy.orm import relationship

Python Modules Imported into catalog_database_setup.py:
	from sqlalchemy import Column, ForeignKey, Integer, String
	from sqlalchemy.ext.declarative import declarative_base
	from sqlalchemy.orm import relationship
	from sqlalchemy import create_engine


Files for this application:
catalog_database_setup.py - creates a database with tables for users, categories, and itmes. 
catalogProject.py - python file to run application
client_secret_catalog.json - client secret for google login
fb_secrets_catalog.json - facebook secret login
Templates - folder for all html templates
	*home.html - public home
	*categoryPage.html - public category page
	*itemPage.html - public item page
	*loggedUser.html - signed in homepage
	*loggedin_categorypage.html - signed in and owner category page
	*loggedin_itemPage.html - signed in and owner item page
	*loggednonOwnerCategoryPage.html - signed in and not owner category page
	*loggednonOwnerItemPage.html - signed in and not owner item page
	*newCategory.html
	*editCategory
	*editItem.html
	*addItem.html
	*deleteItem.html
	*deleteCategory.html
Static - folder holds CSS file
	*styles.css


Guide to Running Application:
1) Install Vagrant and Virtualbox
2) Clone into the repository
3) Launch the Vagrant VM
4) cd into the catalogs directory where catalogProject.py is located
5) run the command "python catalogProject.py"
6) In your browser, navigate to localhost:5000/home
7) You will notice that you are not logged in and the top banner is a beige color
8) You can browse categories without signing in
9) To sign in, click either the Google or Facebook login icons in the top right corner of any page
10) Log in with your credentials and accept the permissions
11) You should then be redirected to the same page you logged in from except now the banner at the top is light blue
12) You can now Add, edit, or delete categories and items (editing/deleting requires that you are the owner of the 
page)
13) If you would like to get a JSON of the data the following are available:
	A) JSON of all categories - go to url /category/json
	B) JSON of all items in category - go to url /<categoryID>/json where <categoryID> is the ID of the category
	C) JSON of an individual item in a category - go to url /<categoryID>/<itemid>/json
	where <categoryID> is the ID of the category and <itemID> is the ID of the item


Enjoy our catalog blog!

Developer:
Matt Shore

