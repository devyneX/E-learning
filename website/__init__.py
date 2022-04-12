from flask import Flask
from flask_login import LoginManager
from flask_mysqldb import MySQL


mysql = MySQL()


def create_app():
    app = Flask(__name__)

    connect_database(app, mysql)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        # return user
        return None

    return app


def connect_database(app, db):
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = ''
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
    app.config['MYSQL_DB'] = 'e_learning'

    db.init(app)
