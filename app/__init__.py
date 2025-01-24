from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin
from flask_babel import Babel
from flask_login import LoginManager

# app and database setup
app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

# database migrations
migrate = Migrate(app, db)

# login manager
login_manager = LoginManager()
login_manager.init_app(app)

#language
def get_locale():
    if request.args.get('lang'):
        session['lang'] = request.args.get('lang')
    return session.get('lang', 'en')

# babel and admin (functionality not implemented)
babel = Babel(app, locale_selector=get_locale)
admin = Admin(app, template_mode='bootstrap4')

# logging for debug
import logging
logging.basicConfig(level=logging.DEBUG)

from app import views, models