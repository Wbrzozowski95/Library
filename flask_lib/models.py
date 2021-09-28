from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from datetime import datetime
from flask import current_app
from flask_lib import db, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


membership = db.Table('membership', db.Model.metadata,
                      db.Column('member_id', db.Integer, db.ForeignKey('user.id')),
                      db.Column('lib_id', db.Integer, db.ForeignKey('library.id'))
                      )


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=False)
    pages = db.Column(db.Integer, nullable=False, default=0)
    days = db.Column(db.Integer, nullable=False, default=0)
    Library = db.relationship('Library', backref='owner', lazy=True, uselist=False)
    Libraries = db.relationship('Library', secondary=membership, backref='member', lazy=True)
    Books = db.relationship('BCopy', backref='owner', lazy=True)

    def get_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)


class Library(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    books = db.relationship('BCopy', backref='part', lazy=True)


class BCopy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False, default='New')
    lend = db.Column(db.Boolean, nullable=False, default=False)
    guest = db.Column(db.Boolean, nullable=False, default=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lib_id = db.Column(db.Integer, db.ForeignKey('library.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    lend_id = db.Column(db.Integer, nullable=True)
    History = db.relationship('History', backref='book', lazy=True)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, unique=True)
    author = db.Column(db.String(100), nullable=False)
    pages = db.Column(db.Integer, nullable=False)
    Copies = db.relationship('BCopy', backref='original', lazy=True)


class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    action = db.Column(db.String(20), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('b_copy.id'), nullable=False)
    username = db.Column(db.String(20), nullable=False)
