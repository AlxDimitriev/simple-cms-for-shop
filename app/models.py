import jwt
from flask import current_app
from time import time
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    level = db.Column(db.Integer)

    def __repr__(self):
        return '<User: {} \n Email: {} \n Level: {}>'.format(
            self.username, self.email, self.level)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def has_edit_rights(self):
        if self.level and self.level > 1:
            return True

    @property
    def has_admin_rights(self):
        if self.level and self.level > 2:
            return True

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), index=True)
    description = db.Column(db.String(512))
    price = db.Column(db.Float, index=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    photo_id = db.Column(db.String(128))

    def __repr__(self):
        return '<Id: {} \n Title: {} \n Group id: {} \n Photo id: {}>'.format(
            self.id, self.title, self.group_id, self.photo_id)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.String(512))
    photo_id = db.Column(db.String(128))
    items = db.relationship('Item', backref='group', lazy='dynamic')

    def __repr__(self):
        return '<name:{} \n id:{}> \n photo_id:{}>'.format(self.name, self.id, self.photo_id)

    def get_items(self):
        return Item.query.filter_by(group_id=self.id)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))