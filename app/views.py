from flask import render_template, flash, redirect, url_for, request, Response, session, send_file, jsonify
from app import app, db, models, admin, login_manager
from .forms import LoginForm, SignUpForm, ProductForm, EditAccountForm, EditPasswordForm
from flask_admin.contrib.sqla import ModelView
from flask_login import login_user, current_user, logout_user, login_required
from .models import Products, Customers, Addresses, Basket, OrderedProducts, ProductImages, CustomerOrders
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

import json
import os
from io import BytesIO
import sqlite3
import logging


# language
def get_locale():
    if request.args.get('lang'):
        session['lang'] = request.args.get('lang')
    return session.get('lang', 'en')

############################################################## - Flask admin, login and account creation

# (admin not implemented)
#admin.add_view(Model(Products, db.session))


# load user by ID
@login_manager.user_loader
def load_user(id):
    return Customers.query.get(int(id))


# unauthorised
@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('/?next=' + request.path)



# signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # create form
    form=SignUpForm()

    if form.validate_on_submit():

        # check if customer email already exists
        if Customers.query.filter_by(email=form.email.data).first():
            flash("Error: Email already in use.", "error")
            return redirect(url_for('signup'))
        
        # assign variables
        fname = form.first_name.data
        lname = form.last_name.data
        email = form.email.data
        password = form.password.data
        address = form.address_line1.data
        city = form.city.data
        postcode = form.postcode.data

        # hash password
        hashed_password = generate_password_hash(password)

        try:
            # add user
            user = Customers(first_name=fname, last_name=lname, email=email, password=hashed_password)
            app.logger.info("attempting add user. %s", email)
            db.session.add(user)
            # flush 
            db.session.flush() #make sure id is populated
            app.logger.info('customer details valid.')

            # add address based on user id
            address = Addresses(customer_id=user.id, address_line1=address, city=city, postcode=postcode)
            db.session.add(address)
            app.logger.info('address details valid.')

            # commit & redirect
            db.session.commit()
            flash("Account successfully created.", "success")
            app.logger.info("user created account successfully.")
            return redirect(url_for('login'))
        
        # rollback
        except:
             db.session.rollback()
             flash("Error: Account not created.", "error")
             
    return render_template("sign-up.html", title="Sign Up", form=form, new=True)


# login
@app.route('/login', methods=['GET', 'POST'])
def login():
    # create form
    form=LoginForm()
    if form.validate_on_submit():
          
          # get instance of user
          email = form.email.data
          password = form.password.data
          user = Customers.query.filter_by(email=email).first()

          # attempt login
          if user and check_password_hash(user.password, password):
               attempt = login_user(user)
               if attempt==True:
                    app.logger.info("user successfully logged in.")
                    return redirect(url_for('all'))
               # an error occured
               else:
                    app.logger.info("correct details, login failed.")
                    flash("Error: login failed.", "warning")

          # invalid details
          else:
                flash("Error: Invalid login details.", "error")

    return render_template("log-in.html", title="Log In", form=form)


# logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


########################################################################### - Profile and Account Management


# profile view
@app.route("/profile")
@login_required
def profile():
    #query user and their orders
     user_products = Products.query.filter_by(owner_id=current_user.id).all()
     orderid = CustomerOrders.query.filter_by(customer_id=current_user.id).all()
     user_orders = OrderedProducts.query.filter_by(order_id = orderid)
     form = EditPasswordForm()
     return render_template('profile.html', title="Your Profile", user=current_user, products=user_products, changepassword=False, orderedproducts = user_orders, form=form)
    # returns changepassword=false to indicate that the change password form should not be displayed 


# edit account
@app.route('/edit-account/<int:id>', methods=['GET', 'POST'])
def editaccount(id):
    # create form and get customer details
    form=EditAccountForm()
    user= models.Customers.query.get(id)
    address = models.Addresses.query.filter_by(customer_id=id).first()

    # pre-populate form
    if request.method == 'GET':
        form.first_name.data = user.first_name
        form.last_name.data = user.last_name
        form.email.data = user.email
        form.address_line1.data = address.address_line1
        form.city.data = address.city
        form.postcode.data = address.postcode
    
    # edit database
    if form.validate_on_submit():
        fname = form.first_name.data 
        lname = form.last_name.data
        email = form.email.data
        addressline1 = form.address_line1.data
        city = form.city.data
        postcode = form.postcode.data

       # encrypted_password = generate_password_hash(password)

        try:
            #edit user
            app.logger.info("attempting edit user. %s", email)
            user.first_name = fname
            user.last_name = lname
            user.email = email
            app.logger.info('customer details edited.')

            #edit address
            address.address_line1 = addressline1
            address.city = city
            address.postcode = postcode
            app.logger.info('address details edited.')
            
            #commit & redirect
            db.session.commit()
            flash("Account edited successfully.", "success")
            app.logger.info("user edited account successfully.")
            return redirect(url_for('profile'))

        #rollback
        except:
             db.session.rollback()
             flash("Error: Account not edited.", "error")
             
    return render_template("sign-up.html", title="Edit Details", form=form, new=False)


# edit password
@app.route('/edit-password/<int:id>/', methods=['GET', 'POST'])
def editpassword(id):
    # create form
    form=EditPasswordForm()

    if form.validate_on_submit():
        # get user
        user=models.Customers.query.get(id)
        app.logger.info("validating..")

        # get old password
        old_password = form.old_password.data
        app.logger.info("recieved old password")

        # check inputted old password hash matches stored hash
        if (check_password_hash(user.password, old_password)):
            app.logger.info("attempting edit password.")
        else:
            flash("Error: Incorrect password.", "error")
            return redirect(url_for('editpassword', id=id))
        
        # edit database
        try:
            # get new password and generate the hash
            new_password = form.new_password.data
            encrypted_password = generate_password_hash(new_password)
            app.logger.info("encrypted new password")

            # assign new password
            user.password = encrypted_password
            app.logger.info('customer password edited.')
       
            # commit & redirect
            db.session.commit()
            flash("Password edited successfully.", "success")
            app.logger.info("user edited account successfully.")
            return redirect(url_for('profile'))
        
        # rollback
        except:
             db.session.rollback()
             flash("Error: Password not edited.", "error")
        
    return render_template('profile.html', title="Your Profile", user=current_user, changepassword=True, form=form)

######################################################################################################################## - Browsing 

# index (login/signup/browsenologin)
@app.route('/')
def index():
       app.logger.info('index route request')
       return render_template("index.html", title="Welcome")


#browse all categories
@app.route("/browse-all", methods=['GET'])
def all():
    all_products = models.Products.query.all()

    if current_user.is_authenticated:
        user_basket = models.Basket.query.filter_by(customer_id=current_user.id)
        return render_template("browse.html", title="Shop", products=all_products, Filter="All Products", current_user=current_user, basket=user_basket)
    else:
        return render_template("browse.html", title="Shop", products=all_products, Filter="All Products", current_user=None)


# browse trainers
@app.route("/trainers", methods=["GET"])
def trainers():
    trainers = Products.query.filter_by(category='Trainers').all()
    if current_user.is_authenticated:
        user_basket = models.Basket.query.filter_by(customer_id=current_user.id)
        return render_template("browse.html", title="Shop", products=trainers, Filter="Trainers", current_user=current_user, basket=user_basket)
    else:
        return render_template("browse.html", title="Shop", products=trainers, Filter="Trainers", current_user=None)


# browse heels
@app.route("/heels", methods=["GET"])
def heels():
    heels = models.Products.query.filter_by(category='Heels').all()
    
    if current_user.is_authenticated:
        user_basket = models.Basket.query.filter_by(customer_id=current_user.id)
        return render_template("browse.html", title="Shop", products=heels, Filter="Heels", current_user=current_user, basket=user_basket)
    else:
        return render_template("browse.html", title="Shop", products=heels, Filter="Heels", current_user=None)


# browse boots
@app.route("/boots", methods=["GET"])
def boots():
    boots = models.Products.query.filter_by(category='Boots').all()
    if current_user.is_authenticated:
        user_basket = models.Basket.query.filter_by(customer_id=current_user.id)
        return render_template("browse.html", title="Shop", products=boots, Filter="Boots", current_user=current_user, basket=user_basket)
    else:
        return render_template("browse.html", title="Shop", products=boots, Filter="Boots", current_user=None)


# browse sandals
@app.route("/sandals", methods=["GET"])
def sandals():
    sandals = models.Products.query.filter_by(category='Sandals').all()
    if current_user.is_authenticated:
        user_basket = models.Basket.query.filter_by(customer_id=current_user.id)
        return render_template("browse.html", title="Shop", products=sandals, Filter="Sandals", current_user=current_user, basket=user_basket)
    else:
        return render_template("browse.html", title="Shop", products=sandals, Filter="Sandals", current_user=None)


######################################################################### Products and Product Interactions

# get product by ID
@app.route('/getproduct/<int:id>', methods=['GET'])
def getproduct(id):
    return Products.query.get_or_404(id)


# get image to display                  
@app.route('/edit-product/<int:id>')     
@app.route('/browse-all/<int:id>')   
def getimage(id): #id is product id to get image for
    product = ProductImages.query.filter_by(product_id=id).first()
    path = product.filename

    return send_file(BytesIO(product.image), mimetype=product.mimetype, as_attachment=False, download_name=product.filename)


# upload product to site
@app.route('/add-product', methods=['GET', 'POST'])
@login_required
def add():

    # create form
    form = ProductForm()

    # get image
    if request.method == 'POST':
         file = request.files['image']
         filename = secure_filename(file.filename)
         mimetype=file.mimetype
        
    if form.validate_on_submit():
        app.logger.info("validating..")
        try:
            # validate price
            if form.price.data < 0:
                flash("price cant be negative")
                return render_template('add-product.html',
                           title='New Product',
                           form=form, new=True)

            # validate quantity
            if form.quantity_available.data < 0:
                flash("quantity cant be negative")
                return render_template('add-product.html',
                           title='New Product',
                           form=form, new=True)

            app.logger.info("creating new product")
            # create new product, add to db 
            product = models.Products(owner_id=current_user.id, product_name=form.name.data, description=form.description.data, price=form.price.data, quantity_available=form.quantity_available.data, category=form.category.data, size=form.size.data)
            db.session.add(product)
            db.session.flush()
            app.logger.info("created product.")

            # read image and upload to images db
            file = request.files['image']
            image_data = file.read()
            filename = secure_filename(file.filename)
            mimetype=file.mimetype
            upload = models.ProductImages(product_id=product.id, image=image_data, filename=filename, mimetype=mimetype)
            db.session.add(upload)
            app.logger.info("uploaded image")

            # commit & redirect
            db.session.commit()
            app.logger.info('new product created.')
            flash('Succesfully added product %s.'%(form.name.data), "success")
            return redirect(url_for("all"))  

        # rollback
        except:
            flash('Error: Product not created.', "warning")
    
    return render_template('add-product.html',
                           title='New Product',
                           form=form, new=True)


# edit uploaded product
@app.route('/edit-product/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    # create form & get product by passed id
    form = ProductForm()
    product = models.Products.query.get_or_404(id)

    # pre-poulate form data
    form.name.data = product.product_name
    form.description.data = product.description
    form.price.data = product.price
    form.quantity_available.data = product.quantity_available
    form.category.data = product.category
    form.size.data = product.size

    if form.validate_on_submit():
        app.logger.info("validating..")

        # validate price
        if form.price.data < 0:
                flash("price cant be negative")
                return render_template('add-product.html',
                           title='Edit Product',
                           form=form, new=False, product=product)

        # validate quantity
        if form.quantity_available.data < 0:
            flash("quantity cant be negative")
            return render_template('add-product.html',
                           title='Edit Product',
                           form=form, new=False, product=product)
        
        app.logger.info("checkpoint A")

        # edit product details
        product.product_name=form.name.data
        product.description=form.description.data 
        product.price=form.price.data
        product.quantity_availabe=form.quantity_available.data
        product.category=form.category.data
        product.size=form.size.data
        app.logger.info("data recieved")

        # commit & redirect
        db.session.commit()
        app.logger.info("SUCCESS. edited product.")
        flash("Succesfully edited Product", "success")
        return redirect(url_for("profile"))

    # rollback 
    else:
            flash('Error: Product not edited.', "warning")
            db.session.rollback()

    return render_template('add-product.html',
                           title='Edit Product',
                           form=form, new=False, product=product)
                         

# delete product and remove it from any baskets
@app.route("/delete/<int:id>")
@login_required
def delete(id):
    try:
        # get product by passed product id
        p = models.Products.query.get_or_404(id)

        # get the product (multiple) instance in the basket and remove however many there is
        productinbasket = models.Basket.query.filter_by(product_id=p.id).all()
        for pib in productinbasket:
            removefrombasket(pib.id)

        # delete from db and commit
        db.session.delete(p)
        db.session.commit()
        flash("Successfully deleted product.", "success")
        
    # rollbacl
    except:
            db.session.rollback()
            flash("Error when deleting.", "warning")

    return redirect(url_for("all"))


# view basket
@app.route("/basket", methods=['GET', 'POST'])
@login_required
def viewbasket():

    # get all products in user basket
    basket_products = Basket.query.filter_by(customer_id=current_user.id).all()

    # initiate price to 0
    totalprice = 0.00
    
    # total price of all products
    for p in basket_products:
        product = Products.query.get_or_404(p.product_id)
        totalprice = totalprice + product.price 
  
    return render_template("basket.html", title="Basket", products=basket_products, current_user=current_user, totalprice=totalprice)


# add product to basket
@app.route("/add-to-basket/<int:id>", methods=['GET', 'POST'])
@login_required
def addtobasket(id): #id = product id
    try:
        # check if product already in basket
        productinbasket = Basket.query.filter_by(customer_id=current_user.id, product_id=id).first() 
        if productinbasket:
            flash("WARNING: Product is already in the basket", "warning")
            return redirect(url_for("all"))

        # add product to basket
        app.logger.info("adding")
        producttoadd = Basket(customer_id=current_user.id, product_id=id) #need to update database with basket schema
        db.session.add(producttoadd)
        app.logger.info("good")

        # commit
        db.session.commit()
        app.logger.info("commited")
        flash("Product added to basket.", "success")   

    # rollback    
    except:
            db.session.rollback()
            app.logger.info("error adding to basket rollback in progress")
            flash("Error when adding to basket.", "warning")

    return redirect(url_for("all"))


# remove product from basket
@app.route("/remove-from-basket/<int:id>" , methods=['GET', 'POST'])
@login_required
def removefrombasket(id): #id = product id
    try:
        # get item in basket
        app.logger.info("attempt")
        productinbasket = Basket.query.filter_by(customer_id=current_user.id, product_id=id).first() #need to update database with basket schema
        app.logger.info("got basket item")

        # delete and commit
        db.session.delete(productinbasket)
        app.logger.info("deleted")
        db.session.commit()
        app.logger.info("committed")
        flash("Product removed from basket.", "success")

    # rollback       
    except:
        db.session.rollback()
        flash("Error when removing from basket.", "warning")

    return redirect(url_for("viewbasket"))


# checkout
@app.route("/checkout")
@login_required
def checkout():
    # get products in basket and shipping address
    basket_products = models.Basket.query.filter_by(customer_id=current_user.id).all()
    app.logger.info("got products")
    shippingadress = models.Addresses.query.filter_by(customer_id=current_user.id).first()
    app.logger.info("got address")

    # calculate price of basket
    totalprice=0.00
    for p in basket_products:
        product = Products.query.get_or_404(p.product_id)
        totalprice = totalprice + product.price 
    
    # create an order and add to session
    order = models.CustomerOrders(customer_id=current_user.id, order_date=datetime.now().date() , shipping_address_id=shippingadress.id, total_price=totalprice, order_complete=False)
    app.logger.info("created order")
    db.session.add(order)
    
    # flush and get order id
    db.session.flush()
    orderid = order.id

    try: 
        for p in basket_products:
            # get product
            product = Products.query.get_or_404(p.product_id)
            
            # check if still available
            if product.quantity_available == 0:
                # rollback, out of stock
                db.session.rollback()
                app.logger.info("product out of stock")
                flash("ERROR: one of your products is out of stock", "error")
                db.session.rollback()
                return redirect(url_for("viewbasket"))
            
            # decrease quantity, add one of product to order
            product.quantity_available = product.quantity_available - 1
            producttoorder = models.OrderedProducts(order_id=orderid, product_id=product.id, quantity=1)
            # add to session
            db.session.add(producttoorder)

            #remove product from basket
            removefrombasket(product.id)

    # error, rollback        
    except: 
        db.session.rollback()

    # commit and redirect
    db.session.commit()
    app.logger.info("Order successful")
    flash("Order successful. Your order #" +str(orderid) +" is being processed and products will be shipped in due course", "success")

    return redirect(url_for("profile"))


# AJAX LIKE BUTTON
@app.route('/like', methods=['POST'])
def like_product():
    try:
        product_id = request.json.get('product_id')
        product = Products.query.get(product_id)
        
        product.likes += 1
        
        db.session.commit()

        return jsonify({"success": True, "likes": product.likes})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
