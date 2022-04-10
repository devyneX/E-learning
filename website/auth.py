from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash


auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        acc_type = request.form.get('type')
        username = request.form.get('username')
        password = request.form.get('password')

    # password_check
    user = None
    if check_password_hash(user.enc_pass, password):
        login_user(user, remember=True)
        return redirect(url_for('views.home'))
    else:
        # incorrect password
        pass

    return render_template('login.html', user=current_user)


@auth.route('/signup')
def signup():
    if request.method == 'POST':
        acc_type = request.form.get('type')
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        username = request.form.get('username')
        email = request.form.get('email')
        password1 = request.form.get('set_pass')
        password2 = request.form.get('confirm_pass')

        # validate if the username and email are unique
        # validate something was inputted in fn and ln
        if password1 == password2 and len(password1) >= 8:
            pass
        else:
            # add user to the data base
            user = None
            login_user(user, remember=True)
            return redirect(url_for('views.home'))
    return render_template('sign_up.html', user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
