import os
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate

from .models import db, User
from config import Config

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Для выполнения данного действия необходимо пройти процедуру аутентификации'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    Migrate(app, db)

    from .auth import auth_bp
    from .books import books_bp
    from .reviews import reviews_bp
    from .collections import collections_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(collections_bp)

    return app
