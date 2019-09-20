from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from datetime import datetime
from flask_lib import db, login_manager, app
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=False)
    lib_id = db.Column('lib_id', db.Integer, db.ForeignKey('library.id'), primary_key=True)
    Libraries = db.relationship('Library', secondary=membership, backref='member', lazy=True)
    Books = db.relationship('Bcopy', backref='owner', lazy=True)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


membership = db.Table('membership',
db.Column('member_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
db.Column('lib_id', db.Integer, db.ForeignKey('library.id'), primary_key=True)
)

class Library(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    books = db.relationship('BCopy', backref='part', lazy=True)


class BCopy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False)
    lending_date = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    return_date = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lib_id = db.Column(db.Integer, db.ForeignKey('library.id'), primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    Copies = db.relationship('BCopy', backref='original', lazy=True)

    def __repr__(self):
        return f"Book('{self.title}', '{self.date_posted}')"
