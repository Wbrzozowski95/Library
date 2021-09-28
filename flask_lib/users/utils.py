import os
import secrets

from PIL import Image

from flask_lib import mail
from flask import url_for, current_app
from flask_mail import Message


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pic', picture_fn)
    out_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(out_size)
    i.save(picture_path)
    return picture_fn


def send_active_email(user):
    token = user.get_token(expires_sec=86400)
    msg = Message('Account activation', sender='noreply.@demo.com', recipients=[user.email])
    msg.body = f'''To active your account, visit the following link:
{url_for('users.active_token', token=token, _external=True)}

If you did not make this request then simply ignore this email
'''
    mail.send(msg)


def send_reset_email(user):
    token = user.get_token()
    msg = Message('Password Reset Request', sender='noreply.@demo.com', recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('users.reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email
'''
    mail.send(msg)
