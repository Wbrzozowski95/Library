from flask import render_template, flash, redirect, url_for, request, abort
from flask_lib import app, db, bcrypt, mail
from flask_lib.forms import RegistrationForm, LoginForm, UpdateAccountForm, BookForm, RequestResetForm, \
    ResetPasswordForm, LendForm, SearchForm, InviteForm
from flask_lib.models import User, Library, Book, BCopy, History
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from datetime import datetime
from PIL import Image
import secrets
import os


@app.route('/')
@app.route('/home')
@login_required
def home():
    page = request.args.get('page', 1, type=int)
    main_lib = Library.query.filter_by(owner_id=current_user.id).first()
    # libs = Library.query.filter_by(member=current_user).paginate(page=page, per_page=5)
    libs = current_user.Libraries
    return render_template('home.html', libs=libs, main_lib=main_lib)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
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
        return redirect(url_for('home'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            if user.active:
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('home'))
            else:
                flash('Account inactive.', 'danger')
        else:
            flash('Login Unsuccessful.', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pic', picture_fn)
    out_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(out_size)
    i.save(picture_path)
    return picture_fn


@app.route('/account', methods=['GET', 'POST'])
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
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pic/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)


@app.route('/book/list', methods=['GET', 'POST'])
@login_required
def book_list():
    page = request.args.get('page', 1, type=int)
    book = Book.query
    form = SearchForm()
    if form.validate_on_submit():
        if form.author.data != '':
            book = book.filter_by(author=form.author.data)
        if form.title.data != '':
            book = book.filter_by(title=form.title.data)
    book = book.paginate(page=page, per_page=5)
    return render_template('book_list.html', title='Book List', form=form, legend='Book List', books=book)


@app.route('/book/add/<int:book_id>', methods=['GET', 'POST'])
@login_required
def add_book(book_id):
    lib = Library.query.filter_by(owner_id=current_user.id).first()
    original = Book.query.filter_by(id=book_id).first()
    bcopy = BCopy(owner=current_user, part=lib, original=original)
    db.session.add(bcopy)
    db.session.commit()
    flash('New Book has been added', 'success')
    return redirect(url_for('home'))


@app.route('/book/new', methods=['GET', 'POST'])
@login_required
def new_book():
    form = BookForm()
    if form.validate_on_submit():
        book = Book(title=form.title.data, author=form.author.data, pages=form.pages.data)
        db.session.add(book)
        db.session.commit()
        flash('New Book has been added', 'success')
        return redirect(url_for('book_list'))
    return render_template('create_book.html', title='New Book', form=form, legend='New Book')


@app.route('/book/<int:book_id>')
@login_required
def book(book_id):
    book = BCopy.query.get_or_404(book_id)
    lib = Library.query.get_or_404(book.lib_id)
    return render_template('book.html', title=book.original.title, book=book, lib=lib)


@app.route('/book/<int:book_id>/<string:status>', methods=['GET'])
@login_required
def update_book(book_id, status):
    book = BCopy.query.get_or_404(book_id)
    if book.owner != current_user:
        abort(403)
    if status == 'Return':
        book.lend = False
        book.guest = False
        #book.return_date = datetime.utcnow
        his = History(date=datetime.utcnow(), action='return', book=book, username='guest')
        db.session.commit()
        flash('Your book status has been updated!', 'success')
    else:
        if not book.lend:
            book.status = status
            db.session.commit()
            flash('Your book status has been updated!', 'success')
    return redirect(url_for('book', book_id=book.id))


@app.route('/book/<int:book_id>/delete', methods=['POST'])
@login_required
def delete_book(book_id):
    book = BCopy.query.get_or_404(book_id)
    if book.owner != current_user:
        abort(403)
    if book.lend:
        flash('You cant delete this book now.', 'danger')
    else:
        db.session.delete(book)
        db.session.commit()
        flash('Your book has been deleted!', 'success')
    return redirect(url_for('home'))


@app.route('/lend/<int:book_id>', methods=['GET', 'POST'])
@login_required
def lend(book_id):
    form = LendForm()
    if form.validate_on_submit():
        book = BCopy.query.get_or_404(book_id)
        if book.owner != current_user:
            abort(403)
        if form.remember.data:
            book.guest = True
            book.lend = True
            #book.lending_date = datetime.utcnow
            his = History(date=datetime.utcnow(), action='lending', book=book, username='guest')
            db.session.add(his)
            db.session.commit()
            return redirect(url_for('home'))
        else:
            user = User.query.filter_by(username=form.username.data).first()
            if user:
                book.lend = True
                # book.lending_date = datetime.utcnow
                lib = Library.query.filter_by(owner_id=user.id).first()
                Lbook = BCopy(lend_id=book.id, owner=current_user, original=book.original, part=lib)
                his = History(date=datetime.utcnow(), action='lending', book=book, username=user.username)
                db.session.add(Lbook)
                db.session.add(his)
                db.session.commit()
                return redirect(url_for('home'))
            else:
                flash('There is no such user.', 'danger')
    return render_template('lend.html', title='Lend', form=form)


@app.route('/book/<int:book_id>/history')
@login_required
def history(book_id):
    page = request.args.get('page', 1, type=int)
    his = History.query.filter_by(book_id=book_id).paginate(page=page, per_page=5)
    book = BCopy.query.get_or_404(book_id)
    lib = Library.query.get_or_404(book.lib_id)
    if lib.owner != current_user:
        abort(403)
    return render_template('history.html', his=his, book=book)


@app.route('/return/<int:book_id>')
@login_required
def return_book(book_id):
    book = BCopy.query.get_or_404(book_id)
    Obook = BCopy.query.get_or_404(book.lend_id)
    lib = Library.query.get_or_404(book.lib_id)
    if lib.owner != current_user:
        abort(403)
    Obook.lend = False
    # Obook.return_date = datetime.utcnow
    his = History(date=datetime.utcnow(), action='return', book=Obook, username=current_user.username)
    db.session.add(his)
    db.session.delete(book)
    db.session.commit()
    flash('Book has been returned.', 'success')
    return redirect(url_for('home'))


@app.route('/library/<int:lib_id>')
@login_required
def library(lib_id):
    page = request.args.get('page', 1, type=int)
    lib = Library.query.get_or_404(lib_id)
    if lib.owner != current_user and lib not in current_user.Libraries:
        flash('You cant view this library.', 'danger')
        return redirect(url_for('home'))
    books = BCopy.query.filter_by(part=lib).paginate(page=page, per_page=5)
    return render_template('library.html', books=books, lib=lib)


@app.route('/library/<int:lib_id>/invite', methods=['GET', 'POST'])
@login_required
def invite(lib_id):
    form = InviteForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        lib = Library.query.filter_by(id=lib_id).first()
        if lib.owner != current_user:
            abort(403)
        user.Libraries.append(lib)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('invite.html', title='Invite', form=form)


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # send_reset_email(user)
        flash('An email has been send to reset your password.', 'info')
        token = user.get_token()
        return redirect(url_for('reset_token', token=token, _external=True))
        # return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_token(token)
    if user is None:
        flash('That is an invalid/expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash(f'Your password has been updated', 'success')
        return redirect(url_for('home'))
    return render_template('reset_token.html', title='Reset Password', form=form)


def send_active_email(user):
    token = user.get_token(expires_sec=86400)
    msg = Message('Account activation', sender='noreply.@demo.com', recipients=[user.email])
    msg.body = f'''To active your account, visit the following link:
{url_for('active_token', token=token, _external=True)}

If you did not make this request then simply ignore this email
'''
    mail.send(msg)


def send_reset_email(user):
    token = user.get_token()
    msg = Message('Password Reset Request', sender='noreply.@demo.com', recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email
'''
    mail.send(msg)


@app.route('/active/<token>', methods=['GET', 'POST'])
def active_token(token):
    user = User.verify_token(token)
    if user is None:
        flash('That is an invalid/expired token', 'warning')
        return redirect(url_for('register'))
    user.active = True
    db.session.commit()
    login_user(user, remember=False)
    flash(f'Your account has been activated', 'success')
    return redirect(url_for('home'))
