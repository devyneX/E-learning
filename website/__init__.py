import MySQLdb
from flask import Flask
from flask_login import LoginManager
from flask_mysqldb import MySQL

mysql = MySQL()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'abcd'

    connect_database(app, mysql)

    from .views import views
    from .auth import auth
    from .models import User

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(
            """SELECT * FROM authorization WHERE account_id = %s""", (id, ))
        result = cur.fetchone()
        cur.close()
        try:
            user = User(result['account_id'], result['account_type'],
                        result['username'], result['email'], result['encrypted_password'])
        except TypeError:
            return None
        return user

    return app


def connect_database(app, db):
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = ''
    # app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
    app.config['MYSQL_DB'] = 'e_learning'

    db.init_app(app)


# CREATE TABLE authorization (
#     account_id int NOT NULL AUTO_INCREMENT,
#     account_type varchar(10),
#     username varchar(255) NOT NULL,
#     email varchar(255) NOT NULL,
#     encrypted_password varchar(255) NOT NULL,
#     PRIMARY KEY (account_id)
# );
