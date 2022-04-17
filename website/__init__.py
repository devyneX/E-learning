from flask import Flask
from flask_login import LoginManager
from flask_mysqldb import MySQL
from .models import User


mysql = MySQL()


def create_app():
    app = Flask(__name__)

    connect_database(app, mysql)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        cur = mysql.connection.cursor()
        cur.execute("""SELECT * FROM authorization WHERE account_id=id""")
        result = cur.fetchall()[0]
        user = User(result['account_id'], result['account_type'],
                    result['email'], result['username'], result['encrypted_password'])
        return user

    return app


def connect_database(app, db):
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = ''
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
    app.config['MYSQL_DB'] = 'e_learning'

    db.init_app(app)
