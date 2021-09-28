from flask import render_template, flash, redirect, url_for, request, Blueprint
from flask_lib import db, bcrypt
from flask_lib.models import User, Library
from flask_login import login_user, current_user, logout_user, login_required

from flask_lib.users.forms import RegistrationForm, LoginForm, UpdateAccountForm, RequestResetForm, ResetPasswordForm
from flask_lib.users.utils import save_picture

users = Blueprint('users', __name__)


@users.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        user.active = True
        db.session.add(user)
        lib = Library(owner=user)
        db.session.add(lib)
        db.session.commit()
        # send_active_email(user)
        login_user(user, remember=False)
        flash('An email has been send to you to active your account.', 'info')
        # db.session.rollback()
        return redirect(url_for('users.login'))
    return render_template('register.html', title='Register', form=form)


@users.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            if user.active:
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('main.home'))
            else:
                flash('Account inactive.', 'danger')
        else:
            flash('Login Unsuccessful.', 'danger')
    return render_template('login.html', title='Login', form=form)


@users.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))


@users.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated.', 'success')
        return redirect(url_for('users.account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pic/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)


@users.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # send_reset_email(user)
        flash('An email has been send to reset your password.', 'info')
        token = user.get_token()
        return redirect(url_for('users.reset_token', token=token, _external=True))
        return redirect(url_for('users.login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@users.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_token(token)
    if user is None:
        flash('That is an invalid/expired token', 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash(f'Your password has been updated', 'success')
        return redirect(url_for('main.home'))
    return render_template('reset_token.html', title='Reset Password', form=form)


@users.route('/active/<token>', methods=['GET', 'POST'])
def active_token(token):
    user = User.verify_token(token)
    if user is None:
        flash('That is an invalid/expired token', 'warning')
        return redirect(url_for('users.register'))
    user.active = True
    db.session.commit()
    login_user(user, remember=False)
    flash(f'Your account has been activated', 'success')
    return redirect(url_for('main.home'))