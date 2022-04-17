from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_mysqldb import MySQLdb
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from . import mysql


auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # acc_type = request.form.get('type')
        username = request.form.get('username')
        password = request.form.get('password')

        # password_check
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(
            """SELECT * FROM authorization WHERE username = %s""", (username, ))
        result = cur.fetchone()
        print(result)
        cur.close()
        if result is not None:
            user = User(result['account_id'], result['account_type'],
                        result['username'], result['email'], result['encrypted_password'])
            if check_password_hash(user.enc_password, password):
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                # incorrect password
                pass
        else:
            pass

    return render_template('login.html', user=current_user)


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # acc_type = request.form.get('type')
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        username = request.form.get('username')
        email = request.form.get('email')
        password1 = request.form.get('set_pass')
        password2 = request.form.get('confirm_pass')

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(
            """SELECT username, email FROM authorization WHERE username = %s OR email = %s""", (username, email))
        result = cur.fetchall()
        print(result)
        cur.close()

        if len(result) > 0:
            pass
        # elif len(firstname) < 2 or len(lastname) < 2:
        #     pass
        elif password1 == password2 and len(password1) < 2:
            pass
        else:
            # add user to the data base
            enc_password = generate_password_hash(password1)
            cur = mysql.connection.cursor()
            cur.execute("""INSERT INTO authorization (account_type, username, email, encrypted_password) VALUES(%s, %s, %s, %s)""",
                        ('student', username, email, enc_password))
            mysql.connection.commit()
            # print(username)
            cur.execute(
                """SELECT account_id FROM authorization WHERE username = %s""", (username, ))
            account_id = cur.fetchone()
            print(account_id)
            user = User(
                account_id, 'student', email, username, enc_password)
            login_user(user, remember=True)
            return redirect(url_for('views.home'))
    return render_template('sign_up.html', user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
