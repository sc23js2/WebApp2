from app import db
from flask_login import UserMixin

class Customers(UserMixin, db.Model):
    __tablename__='Customers'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False) 
    password = db.Column(db.String(200), nullable=False) 

class Addresses(db.Model):
    __tablename__='Addresses'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'), nullable=False)
    address_line1 = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(30), nullable=False)
    postcode = db.Column(db.String(10), nullable=False) 

class CustomerOrders(db.Model):
    __tablename__='Customerorders'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'), nullable=False)
    order_date = db.Column(db.Date, nullable=False)
    shipping_address_id = db.Column(db.Integer, db.ForeignKey('Addresses.id'), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    order_complete = db.Column(db.Boolean, default=False)

class OrderedProducts(db.Model):
    __tablename__='Orderedproducts'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('Customerorders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('Products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
   
class Products(db.Model):
    __tablename__='Products'
    id = db.Column(db.Integer, primary_key=True) 
    owner_id = db.Column(db.Integer, db.ForeignKey('Customers.id'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity_available = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(30), nullable=False, index=True) 
    size = db.Column(db.String(5), nullable=False) 
    likes = db.Column(db.Integer, default=0)

class ProductImages(db.Model):
    __tablename__='Productimages'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('Products.id'), nullable=False, index=True)
    image = db.Column(db.LargeBinary, nullable=False)
    filename = db.Column(db.String(150), nullable=False)
    mimetype=db.Column(db.Text, nullable=False)
    
class Basket(db.Model):
    __tablename__='Basket'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('Products.id'), nullable=False)