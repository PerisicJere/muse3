from flask import Blueprint, render_template, request, flash, redirect, url_for
from . import db
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash, gen_salt
from flask_login import login_user, login_required, logout_user, current_user
auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        displayName = request.form.get('displayName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash("Email is not valid", category='error')
        elif not displayName or len(displayName) < 2:
            flash('Display name should be at least 2 characters long', category='error')
        elif len(password1) <= 8:
            flash('Password is shorter than 8 characters', category='error')
            print(generate_password_hash(password1, method="pbkdf2:sha256"))
        elif password1 != password2:
            flash("Passwords don't match", category='error')
        else:
            new_user = User(email=email, password=generate_password_hash(password1, method="pbkdf2:sha256"),
                            displayName=displayName)
            db.session.add(new_user)
            db.session.commit()
            flash('Account is created!')
            return redirect(url_for('views.home'))
    return render_template("sign_up.html", user=current_user)
