from flask import render_template, flash, redirect, url_for, request, abort, Blueprint
from flask_lib import db
from flask_lib.books.forms import SearchForm, BookForm, LendForm
from flask_lib.models import User, Library, Book, BCopy, History
from flask_login import current_user, login_required
from datetime import datetime

books = Blueprint('books', __name__)


@books.route('/book/list', methods=['GET', 'POST'])
@login_required
def book_list():
    page = request.args.get('page', 1, type=int)
    book = Book.query
    form = SearchForm()
    if form.validate_on_submit() or request.args.get('page', 1, type=int):
        if request.values.get("author"):
            form.author.data=request.values.get("author")
            search = '%{}%'.format(form.author.data.upper())
            book = book.filter(Book.author.like(search))
        if request.values.get("title"):
            form.title.data = request.values.get("title")
            search = '%{}%'.format(form.title.data.upper())
            book = book.filter(Book.title.like(search))
    book = book.paginate(page=page, per_page=2, error_out=False)
    return render_template('book_list.html', title='Book List', form=form, legend='Book List', books=book)


@books.route('/book/add/<int:book_id>', methods=['GET', 'POST'])
@login_required
def add_book(book_id):
    lib = Library.query.filter_by(owner_id=current_user.id).first()
    original = Book.query.filter_by(id=book_id).first()
    bcopy = BCopy(owner=current_user, part=lib, original=original)
    db.session.add(bcopy)
    db.session.commit()
    flash('New Book has been added', 'success')
    return redirect(url_for('main.library', lib_id=current_user.Library.id))


@books.route('/book/new', methods=['GET', 'POST'])
@login_required
def new_book():
    form = BookForm()
    if form.validate_on_submit():
        book = Book(title=form.title.data.upper(), author=form.author.data.upper(), pages=form.pages.data)
        db.session.add(book)
        db.session.commit()
        flash('New Book has been added', 'success')
        return redirect(url_for('books.book_list'))
    return render_template('create_book.html', title='New Book', form=form, legend='New Book')


@books.route('/book/<int:book_id>')
@login_required
def book(book_id):
    book = BCopy.query.get_or_404(book_id)
    lib = Library.query.get_or_404(book.lib_id)
    return render_template('book.html', title=book.original.title, book=book, lib=lib)


@books.route('/book/<int:book_id>/<string:status>', methods=['GET'])
@login_required
def update_book(book_id, status):
    book = BCopy.query.get_or_404(book_id)
    if book.owner != current_user:
        abort(403)
    if status == 'Return':
        book.lend = False
        book.guest = False
        his = History(date=datetime.utcnow(), action='return', book=book, username='guest')
        db.session.commit()
        flash('Your book status has been updated!', 'success')
    if status == 'Reading':
        book.status = status
        book.date = datetime.utcnow()
        db.session.commit()
        flash('Your book status has been updated!', 'success')
    if status == 'Finished':
        if book.status == 'Reading':
            delta = datetime.utcnow()-book.date
            current_user.days += delta.days
        current_user.pages += book.original.pages
        book.status = status
        db.session.commit()
        flash('Your book status has been updated!', 'success')
    return redirect(url_for('books.book', book_id=book.id))


@books.route('/book/<int:book_id>/delete', methods=['POST'])
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
    return redirect(url_for('main.library', lib_id=current_user.Library.id))


@books.route('/lend/<int:book_id>', methods=['GET', 'POST'])
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
            his = History(date=datetime.utcnow(), action='lending', book=book, username='guest')
            db.session.add(his)
            db.session.commit()
            return redirect(url_for('main.library', lib_id=current_user.Library.id))
        else:
            user = User.query.filter_by(username=form.username.data).first()
            if user:
                book.lend = True
                lib = Library.query.filter_by(owner_id=user.id).first()
                Lbook = BCopy(lend_id=book.id, owner=current_user, original=book.original, part=lib)
                his = History(date=datetime.utcnow(), action='lending', book=book, username=user.username)
                db.session.add(Lbook)
                db.session.add(his)
                db.session.commit()
                return redirect(url_for('main.library', lib_id=current_user.Library.id))
            else:
                flash('There is no such user.', 'danger')
    return render_template('lend.html', title='Lend', form=form)


@books.route('/book/<int:book_id>/history')
@login_required
def history(book_id):
    page = request.args.get('page', 1, type=int)
    his = History.query.filter_by(book_id=book_id).paginate(page=page, per_page=5)
    book = BCopy.query.get_or_404(book_id)
    lib = Library.query.get_or_404(book.lib_id)
    if lib.owner != current_user:
        abort(403)
    return render_template('history.html', his=his, book=book)


@books.route('/return/<int:book_id>')
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
    return redirect(url_for('main.library', lib_id=current_user.Library.id))

