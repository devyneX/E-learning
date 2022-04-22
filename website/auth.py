from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_mysqldb import MySQLdb
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from datetime import date
from . import mysql


auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # fetching info from the form
        acc_type = request.form.get('type')
        username = request.form.get('username')
        password = request.form.get('password')

        # fetching info from db
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(
            """SELECT * FROM authorization WHERE username = %s AND account_type = %s""", (username, acc_type))
        result = cur.fetchone()
        print(result)
        cur.close()
        # if the user exists
        if result is not None:
            user = User(result['account_id'], result['account_type'],
                        result['username'], result['email'], result['encrypted_password'])
            # checking password
            if check_password_hash(user.enc_password, password):
                login_user(user, remember=True)
                return redirect(url_for('views.profile'))
            else:
                # incorrect password
                flash('Incorrect Password', 'error')
                return render_template('login.html', user=current_user)
        else:
            # if the user does not exist, redirect to sign up page
            return redirect(url_for('auth.signup'))

    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('views.profile'))
        else:
            return render_template('login.html', user=current_user)


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    # fetching info from the form
    if request.method == 'POST':
        acc_type = request.form.get('type')
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        username = request.form.get('username')
        email = request.form.get('email')
        password1 = request.form.get('set_pass')
        password2 = request.form.get('confirm_pass')

        # fetching info from db
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(
            """SELECT username, email FROM authorization WHERE (username = %s OR email = %s) and account_type = %s""", (username, email, acc_type))
        result = cur.fetchall()
        print(result)
        cur.close()

        # checking if the username and email are unique
        if len(result) > 0:
            # flash
            flash('Username/Email already exists', 'error')
            return render_template('sign_up.html', user=current_user)
        # checking if valid names were inputted
        elif len(firstname) < 2 or len(lastname) < 2:
            # flash
            flash('Input a valid first name and last name', 'error')
            return render_template('sign_up.html', user=current_user)
        # checking length of the password
        elif len(password1) < 2:
            # flash
            flash('Password too small', 'error')
            return render_template('sign_up.html', user=current_user)
        # checking if the two passwords match
        elif password1 != password2:
            flash("Passwords don't match", 'error')
            return render_template('sign_up.html', user=current_user)

        else:
            # add user to the data base
            enc_password = generate_password_hash(password1)
            cur = mysql.connection.cursor()
            cur.execute("""INSERT INTO authorization (account_type, username, email, encrypted_password) VALUES(%s, %s, %s, %s)""",
                        (acc_type, username, email, enc_password))
            mysql.connection.commit()

            cur.execute(
                """SELECT account_id FROM authorization WHERE username = %s AND account_type = %s ORDER BY account_id DESC""", (username, acc_type))
            account_id = cur.fetchone()[0]

            if acc_type == 'student':
                cur.execute("""INSERT INTO student (firstname, lastname, join_date, account_id) VALUES (%s, %s, %s, %s)""",
                            (firstname, lastname, date.today(), account_id))
            else:
                cur.execute("""INSERT INTO teacher (firstname, lastname, join_date, account_id) VALUES (%s, %s, %s, %s)""",
                            (firstname, lastname, date.today(), account_id))

            mysql.connection.commit()
            user = User(
                account_id, 'student', email, username, enc_password)
            login_user(user, remember=True)
            return redirect(url_for('views.profile'))

    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect('views.profile')
        else:
            return render_template('sign_up.html', user=current_user)


@auth.route('/update_account', methods=['POST'])
@login_required
def update_account():
    username = request.form.get('username')
    email = request.form.get('email')
    old_pass = request.form.get('old_password')
    new_pass = request.form.get('new_password')
    confirm_pass = request.form.get('confirm_password')

    if check_password_hash(current_user.enc_password, old_pass):
        cur = mysql.connection.cursor()
        if username != current_user.username:
            cur.execute("""UPDATE authorization SET username = %s WHERE account_id = %s""",
                        (username, current_user.account_id))
            mysql.connection.commit()
            current_user.username = username
        if email != current_user.username:
            cur.execute("""UPDATE authorization SET email = %s WHERE account_id = %s""",
                        (email, current_user.account_id))
            mysql.connection.commit()
            current_user.email = email

        if new_pass is not None:
            if new_pass == confirm_pass:
                cur.execute("""UPDATE authorization SET encrypted_password = %s WHERE account_id = %s""",
                            (generate_password_hash(new_pass), current_user.account_id))
                mysql.connection.commit()
                current_user.enc_password = generate_password_hash(new_pass)

        return redirect(url_for('views.account'))


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
