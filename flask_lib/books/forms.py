from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange


class BookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=0, max=100)])
    author = StringField('Author', validators=[DataRequired(), Length(min=0, max=100)])
    pages = IntegerField('Pages', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Add')


class LendForm(FlaskForm):
    username = StringField('Username', validators=[Length(min=2, max=20)])
    remember = BooleanField('Guest')
    submit = SubmitField('Lend')


class SearchForm(FlaskForm):
    author = StringField('Author', default='')
    title = StringField('Title', default='')
    submit = SubmitField('Search')