from flask import render_template, flash, redirect, url_for, request, Response, session, send_file, send_from_directory
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

##############################################################flask admin
#admin.add_view(Model(Products, db.session))

def get_locale():
    if request.args.get('lang'):
        session['lang'] = request.args.get('lang')
    return session.get('lang', 'en')

############################################################flask login
@login_manager.user_loader
def load_user(id):
    return Customers.query.get(int(id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
          email = form.email.data
          password = form.password.data
          user = Customers.query.filter_by(email=email).first()

          if user and check_password_hash(user.password, password):
               attempt = login_user(user)
               if attempt==True:
                    app.logger.info("user successfully logged in.")
                    return redirect(url_for('all'))
               else:
                    app.logger.info("correct details, login failed.")
                    flash("Error: login failed.", "warning")
          else:
                flash("Error: Invalid login details.", "error")

    return render_template("log-in.html", title="Log In", form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form=SignUpForm()

    if form.validate_on_submit():

        if Customers.query.filter_by(email=form.email.data).first():
            flash("Error: Email already in use.", "error")
            return redirect(url_for('signup'))
        
        fname = form.first_name.data
        lname = form.last_name.data
        email = form.email.data
        password = form.password.data
        address = form.address_line1.data
        city = form.city.data
        postcode = form.postcode.data

        hashed_password = generate_password_hash(password)

        try:
            #add user
            app.logger.info("attempting add user. %s", email)
            user = Customers(first_name=fname, last_name=lname, email=email, password=hashed_password)
            db.session.add(user)
            db.session.flush() #make sure id is populated
            app.logger.info('customer details valid.')
            #add address based on user id
            address = Addresses(customer_id=user.id, address_line1=address, city=city, postcode=postcode)
            db.session.add(address)
            app.logger.info('address details valid.')
            #commit
            db.session.commit()
            flash("Account successfully created.", "success")
            app.logger.info("user created account successfully.")
            return redirect(url_for('login'))
        except:
             db.session.rollback()
             flash("Error: Account not created.", "error")
             
    return render_template("sign-up.html", title="Sign Up", form=form, new=True)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('/?next=' + request.path)

#########################################################################profile

@app.route("/profile")
@login_required
def profile():
     user_products = Products.query.filter_by(owner_id=current_user.id).all()
     orderid = CustomerOrders.query.filter_by(customer_id=current_user.id).all()
     user_orders = OrderedProducts.query.filter_by(order_id = orderid)
     form = EditPasswordForm()
     return render_template('profile.html', title="Your Profile", user=current_user, products=user_products, changepassword=False, orderedproducts = user_orders, form=form)

@app.route('/edit-account/<int:id>', methods=['GET', 'POST'])
def editaccount(id):
    form=EditAccountForm()
    user= models.Customers.query.get(id)
    address = models.Addresses.query.filter_by(customer_id=id).first()

    if request.method == 'GET':
        form.first_name.data = user.first_name
        form.last_name.data = user.last_name
        form.email.data = user.email
        form.address_line1.data = address.address_line1
        form.city.data = address.city
        form.postcode.data = address.postcode
    
    if form.validate_on_submit():
        fname = form.first_name.data 
        lname = form.last_name.data
        email = form.email.data
        addressline1 = form.address_line1.data
        city = form.city.data
        postcode = form.postcode.data

       # encrypted_password = generate_password_hash(password)

        try:
            #add user
            app.logger.info("attempting edit user. %s", email)
            user.first_name = fname
            user.last_name = lname
            user.email = email
           # user.password = encrypted_password
            app.logger.info('customer details edited.')
            #edit address
            address.address_line1 = addressline1
            address.city = city
            address.postcode = postcode
            db.session.commit()
            app.logger.info('address details edited.')
            #commit
            flash("Account edited successfully.", "success")
            app.logger.info("user edited account successfully.")
            return redirect(url_for('profile'))
        except:
             db.session.rollback()
             flash("Error: Account not edited.", "error")
             
    return render_template("sign-up.html", title="Edit Details", form=form, new=False)

@app.route('/edit-password/<int:id>/', methods=['GET', 'POST'])
def editpassword(id):
    form=EditPasswordForm()

    if form.validate_on_submit():
        user=models.Customers.query.get(id)
        app.logger.info("validating..")

        new_password = form.new_password.data
        encrypted_password = generate_password_hash(new_password)

        old_password = form.old_password.data
        
        app.logger.info("recieved passwords")

        if (check_password_hash(user.password, old_password)):
            app.logger.info("attempting edit password.")
        else:
            flash("Error: Incorrect password.", "error")
            return redirect(url_for('editpassword', id=id))
        
        try:
            #add user
            app.logger.info("attempting edit password.")
            user.password = encrypted_password
            app.logger.info('customer password edited.')
            #edit address
            db.session.commit()
           
            #commit
            flash("Password edited successfully.", "success")
            app.logger.info("user edited account successfully.")
            return redirect(url_for('profile'))
        except:
             db.session.rollback()
             flash("Error: Password not edited.", "error")
        
    return render_template('profile.html', title="Your Profile", user=current_user, changepassword=True, form=form)

########################################################################## home
@app.route('/')
def index():
       app.logger.info('index route request')
       return render_template("index.html", title="Welcome")

######################################################################### filter assesments
@app.route("/browse-all", methods=['GET'])
def all():
    all_products = models.Products.query.all()

    if current_user.is_authenticated:
        user_basket = models.Basket.query.filter_by(customer_id=current_user.id)
        return render_template("browse.html", title="Shop", products=all_products, Filter="All Products", current_user=current_user, basket=user_basket)
    else:
        return render_template("browse.html", title="Shop", products=all_products, Filter="All Products", current_user=None)


@app.route("/browse-trainers", methods=["GET"])
def trainers():
    trainers = Products.query.filter_by(category='Trainers').all()
    if current_user.is_authenticated:
        user_basket = models.Basket.query.filter_by(customer_id=current_user.id)
        return render_template("browse.html", title="Shop", products=trainers, Filter="Trainers", current_user=current_user, basket=user_basket)
    else:
        return render_template("browse.html", title="Shop", products=trainers, Filter="Trainers", current_user=None)

@app.route("/heels", methods=["GET"])
def heels():
    heels = models.Products.query.filter_by(category='Heels').all()
    
    if current_user.is_authenticated:
        user_basket = models.Basket.query.filter_by(customer_id=current_user.id)
        return render_template("browse.html", title="Shop", products=heels, Filter="Heels", current_user=current_user, basket=user_basket)
    else:
        return render_template("browse.html", title="Shop", products=heels, Filter="Heels", current_user=None)

@app.route("/boots", methods=["GET"])
def boots():
    boots = models.Products.query.filter_by(category='Boots').all()
    if current_user.is_authenticated:
        user_basket = models.Basket.query.filter_by(customer_id=current_user.id)
        return render_template("browse.html", title="Shop", products=boots, Filter="Boots", current_user=current_user, basket=user_basket)
    else:
        return render_template("browse.html", title="Shop", products=boots, Filter="Boots", current_user=None)

@app.route("/sandals", methods=["GET"])
def sandals():
    sandals = models.Products.query.filter_by(category='Sandals').all()
    if current_user.is_authenticated:
        user_basket = models.Basket.query.filter_by(customer_id=current_user.id)
        return render_template("browse.html", title="Shop", products=sandals, Filter="Sandals", current_user=current_user, basket=user_basket)
    else:
        return render_template("browse.html", title="Shop", products=sandals, Filter="Sandals", current_user=None)
######################################################################### buttons
@app.route("/delete/<int:id>")
@login_required
def delete(id):
    try:
        p = models.Products.query.get_or_404(id)
        db.session.delete(p)
        db.session.commit()
        flash("Successfully deleted product.", "success")
           
    except:
            db.session.rollback()
            flash("Error when deleting.", "warning")

    return redirect(url_for("all"))

######################################################################### Products
@app.route('/add-product', methods=['GET', 'POST'])
@login_required
def add():
    form = ProductForm()
    if request.method == 'POST':
         file = request.files['image']
         filename = secure_filename(file.filename)
         mimetype=file.mimetype
        
    if form.validate_on_submit():
        app.logger.info("validating..")
        try:
            if form.price.data < 0:
                flash("price cant be negative")
                return render_template('add-product.html',
                           title='New Product',
                           form=form, new=True)

            if form.quantity_available.data < 0:
                flash("quantity cant be negative")
                return render_template('add-product.html',
                           title='New Product',
                           form=form, new=True)

            app.logger.info("creating new product")
            product = models.Products(owner_id=current_user.id, product_name=form.name.data, description=form.description.data, price=form.price.data, quantity_available=form.quantity_available.data, category=form.category.data, size=form.size.data) #, image=form.image.data )
            db.session.add(product)
            db.session.flush()
            app.logger.info("created product.")

            file = request.files['image']
            image_data = file.read()
            filename = secure_filename(file.filename)
            mimetype=file.mimetype
            
            upload = models.ProductImages(product_id=product.id, image=image_data, filename=filename, mimetype=mimetype)
            
            db.session.add(upload)
            app.logger.info("uploaded image")

            app.logger.info("saved image")

            db.session.commit()
            app.logger.info('new product created.')
            flash('Succesfully added product %s.'%(form.name.data), "success")
            return redirect(url_for("all"))  
        except:
            flash('Error: Product not created.', "warning")
    
    return render_template('add-product.html',
                           title='New Product',
                           form=form, new=True)


@app.route('/edit-product/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    form = ProductForm()
    product = models.Products.query.get_or_404(id)

    form.name.data = product.product_name
    form.description.data = product.description
    form.price.data = product.price
    form.quantity_available.data = product.quantity_available
    form.category.data = product.category
    form.size.data = product.size

    if form.validate_on_submit():
        
        app.logger.info("checkpoint A")
        product.product_name=form.name.data
        product.description=form.description.data 
        product.price=form.price.data
        product.quantity_availabe=form.quantity_available.data
        product.category=form.category.data
        product.size=form.size.data

        app.logger.info("data recieved")

        db.session.commit()
    

        flash("Succesfully edited Product", "success")
        return redirect(url_for("all"))
        
    else:
            flash('Error: Product not edited.', "warning")

    return render_template('add-product.html',
                           title='Edit Product',
                           form=form, new=False, product=product)
                            #form=form form.name.data=product.title form.name.description= .....

                        
@app.route('/edit-product/<int:id>')     
@app.route('/browse-all/<int:id>')   
def getimage(id): #id is product id to get image for
    product = ProductImages.query.filter_by(product_id=id).first()
    path = product.filename

    #app.logger.info(.image)
    return send_file(BytesIO(product.image), mimetype=product.mimetype, as_attachment=False, download_name=product.filename)


@app.route("/add-to-basket/<int:id>", methods=['GET', 'POST'])
@login_required
def addtobasket(id): #id = product id
    try:
        app.logger.info("adding")
        producttoadd = Basket(customer_id=current_user.id, product_id=id) #need to update database with basket schema
        
        db.session.add(producttoadd)
        app.logger.info("good")
        #app.logger.info(producttoadd.product_id)

        #db.session.flush()
        #db.session.add(producttoadd)
        
        db.session.commit()
        app.logger.info("commited")

        flash("Product added to basket.", "success")       
    except:
            db.session.rollback()
            app.logger.info("error adding to basket rollback in progress")
            flash("Error when adding to basket.", "warning")

    return redirect(url_for("all"))


@app.route("/remove-from-basket/<int:id>")
@login_required
def removefrombasket(id): #id = product id
    try:
        productinbasket = Basket.query.get_or_404(customer_id=current_user.id, product_id=id) #need to update database with basket schema
        db.session.delete(productinbasket)
        db.session.commit()
        flash("Product removed from basket.", "success")
           
    except:
        db.session.rollback()
        flash("Error when removing from basket.", "warning")

    return redirect(url_for("viewbasket"))


@app.route("/basket")
@login_required
def viewbasket():
    basket_products = models.Basket.query.filter_by(customer_id=current_user.id).all()

    totalprice = 0.00
    for p in basket_products:
         totalprice = totalprice + p.price
    return render_template("basket.html", title="Basket", products=basket_products, current_user=current_user, totalprice=totalprice)

@app.route("/checkout/<float:totalprice>")
@login_required
def checkout(totalprice):
    basket_products = models.Basket.query.filter_by(customer_id=current_user.id).all()
    
    shippingadress = models.Addresses.query.filter_by(customer_id=current_user.id).first()

    order = models.CustomerOrders(customer_id=current_user.id, order_date=datetime.now().date, shipping_address_id=shippingadress.id, total_price=totalprice, order_complete=False)
    db.session.add(order)
    db.session.flush()

    orderid = order.id

    for p in basket_products:

        if p.quantity == 0:
            db.session.rollback()
            app.logger.info("product out of stock")
            flash("ERROR: one of your products is out of stock", "error")
            return redirect(url_for(viewbasket))
        
        p.quantity = p.quantity - 1
        producttoorder = models.OrderedProducts(order_id=orderid, product_id=p.id, quantity=1)
        db.session.add(producttoorder)
        
    db.session.commit()
    app.logger.info("Order successful")
    flash("Order successful. Your order #%s is being processed and products will be shipped in due course" + orderid , "success")

    return redirect(url_for(profile))


##AJAX LIKE BUTTON
@app.route('/like/<int:id>', methods=['POST'])
def like(id):
        # Load the JSON data and use the ID of the idea that was clicked to get the object
    data = json.loads(request.data)
    product_id = int(data.get('product_id'))
    product = models.Products.query.get(product_id)

    # Increment the correct vote
    
    product.likes += 1

        # Save the updated vote count in the DB
    db.session.commit()
        # Tell the JS .ajax() call that the data was processed OK
    return json.dumps({'status':'OK','Likes': product.likes})

     

     
    