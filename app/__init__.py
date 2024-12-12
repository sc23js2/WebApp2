from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin
from flask_babel import Babel
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

migrate = Migrate(app, db)

def get_locale():
    if request.args.get('lang'):
        session['lang'] = request.args.get('lang')
    return session.get('lang', 'en')

babel = Babel(app, locale_selector=get_locale)
admin = Admin(app, template_mode='bootstrap4')

import logging
logging.basicConfig(level=logging.DEBUG)

from app import views, models