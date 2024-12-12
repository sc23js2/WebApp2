from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, DateField, TextAreaField, DecimalField, IntegerField, FileField, EmailField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Regexp, Email
from flask_wtf.file import FileRequired, FileAllowed

class SignUpForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(2, 30, message='i.e. John')])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(2, 30, message='i.e. Doe')])
    email = EmailField('Email Address', validators=[DataRequired(), Email(), Length(10, 50, message='i.e. johndoe@gmail.com')])
    address_line1 = StringField('Address Line 1', validators=[DataRequired(), Length(2, 30, message="i.e. 123 Malory Street")])
    city = StringField('City', validators=[DataRequired(), Length(2, 30, message='i.e. Leeds')])
    postcode = StringField('Postcode', validators=[DataRequired(), Regexp(r'^[A-Z0-9 ]{5,8}$', message='Invalid postcode format.')]) 
    password = StringField('Password', validators=[DataRequired(), Length(2, 30, message='Its a secret.')]) #regex
    submit = SubmitField('Confirm')
 
class LoginForm(FlaskForm):
    email = EmailField('Email Address', validators=[DataRequired(), Email(), Length(10, 40, message="name@domain.x.y")])
    password = PasswordField('Password', validators=[DataRequired(), Length(7, 30, message="Password must be between 7-30 characters.")]) #regex
    submit = SubmitField('Log In')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(5, 100, message='Product Name')])
    description = TextAreaField('Description', validators=[DataRequired(), Length(10, 1000, message='Descscribe your product..')])
    price = DecimalField('Price', validators=[DataRequired()])
    quantity_available = IntegerField('Quantity availible to sell.', validators=[DataRequired()])
    category = SelectField('Product Category', choices=[('Trainers'), ('Boots'), ('Heels'), ('Sandals')], validators=[DataRequired()])
    size = SelectField('Product Size', choices=[('EU35', 'UK3'), ('EU36', 'UK3.5'), ('EU37', 'UK4'), ('EU37.5', 'UK4.5'), ('EU38', 'UK5'), ('EU39', 'UK5.5'), ('EU39.5', 'UK6'), ('EU40', 'UK6.5'), ('EU41', 'UK7'), ('EU41.5', 'UK7.5'), ('EU42', 'UK8'), ('EU42.5', 'UK8.5'), ('EU43', 'UK9'), ('EU44', 'UK9.5'), ('EU44.5', 'UK10')], validators=[DataRequired()])
    image = FileField('Product Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], "Images Only.")])
    submit = SubmitField('Upload Item')
 
class EditAccountForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(2, 30, message='i.e. John')])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(2, 30, message='i.e. Doe')])
    email = EmailField('Email Address', validators=[DataRequired(), Email(), Length(10, 50, message='i.e. johndoe@gmail.com')])
    address_line1 = StringField('Address Line 1', validators=[DataRequired(), Length(2, 30, message="i.e. 123 Malory Street")])
    city = StringField('City', validators=[DataRequired(), Length(2, 30, message='i.e. Leeds')])
    postcode = StringField('Postcode', validators=[DataRequired(), Regexp(r'^[A-Z0-9 ]{5,8}$', message='Invalid postcode format.')]) 
    submit = SubmitField('Confirm')
 
class EditPasswordForm(FlaskForm):
    old_password = PasswordField('Current Password', validators=[DataRequired(), Length(2, 30, message='Its a secret.')])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(2, 30, message='Its a secret.')])
    submit = SubmitField('Update Password')
    
#def checkPassword(request, id)
    #form=assesment(request.post)