from flask import render_template, flash, redirect, url_for, request, abort, Blueprint
from flask_lib import db
from flask_lib.main.forms import InviteForm
from flask_lib.models import User, Library, BCopy
from flask_login import current_user, login_required

main = Blueprint('main', __name__)


@main.route('/')
@main.route('/home')
@login_required
def home():
    page = request.args.get('page', 1, type=int)
    main_lib = Library.query.filter_by(owner_id=current_user.id).first()
    # libs = Library.query.filter_by(member=current_user).paginate(page=page, per_page=5)
    libs = current_user.Libraries
    return render_template('home.html', libs=libs, main_lib=main_lib)


@main.route('/library/<int:lib_id>')
@login_required
def library(lib_id):
    page = request.args.get('page', 1, type=int)
    lib = Library.query.get_or_404(lib_id)
    user = lib.owner
    if user != current_user and lib not in current_user.Libraries:
        flash('You cant view this library.', 'danger')
        return redirect(url_for('main.home'))
    books = BCopy.query.filter_by(part=lib).paginate(page=page, per_page=5)
    data = {'Reading': 0, 'Finished': 0, 'Lend': 0, 'New': 0, 'PD': 0}
    for book in books.items:
        if book.lend:
            data['Lend'] += 1
        else:
            data[book.status] += 1
    if user.days > 0:
        data['PD'] = user.pages / user.days
    return render_template('library.html', books=books, lib=lib, data=data)


@main.route('/library/<int:lib_id>/invite', methods=['GET', 'POST'])
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
        return redirect(url_for('main.home'))
    return render_template('invite.html', title='Invite', form=form)
