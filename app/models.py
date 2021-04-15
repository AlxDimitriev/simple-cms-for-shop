import jwt, base64, os
from flask import current_app, url_for
from time import time
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.search import add_to_index, remove_from_index, query_index
from datetime import datetime, timedelta
from app.utils import upload_photo


class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        if not current_app.elasticsearch: # or any other search engine, which you'll use
            return
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)


class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page, per_page, False)
        data = {
            'items': [item.to_dict(to_collection=True) for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page,
                                **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                                **kwargs) if resources.has_prev else None
            }
        }
        return data


class User(PaginatedAPIMixin, UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    permission = db.Column(db.String(32))
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)

    def __repr__(self):
        return '<User: {} \n Email: {} \n Permission: {}>'.format(
            self.username, self.email, self.permission)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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

    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'permission': self.permission,
            '_links': {
                'self': url_for('api.get_user', id=self.id),
                'get_users': url_for('api.get_users')
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
        for field in ['username', 'email', 'permission']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])

    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user


class Item(PaginatedAPIMixin, SearchableMixin, db.Model):
    __searchable__ = ['title']
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), index=True)
    description = db.Column(db.String(512))
    price = db.Column(db.Float, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    photo_id = db.Column(db.String(128))

    def __repr__(self):
        return '<Id: {} \n Title: {} \n Category id: {} \n Photo id: {}>'.format(
            self.id, self.title, self.category_id, self.photo_id)

    def to_dict(self, to_collection=False):
        thumbnail_size = 500
        if to_collection:
            thumbnail_size = 120
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'price': self.price,
            'category_id': self.category_id,
            'photo_data': self.get_thumbnail(self.photo_id, thumbnail_size, url=False),
            '_links': {
                'self': url_for('api.get_item', id=self.id),
                'category': url_for('api.get_category', id=self.category_id)
            }
        }
        return data

    def from_dict(self, data):
        for field in ['title', 'description', 'price', 'category_id']:
            if field in data:
                setattr(self, field, data[field])
            if 'photo_data' in data:
                image = base64.b64decode(data['photo_data'])
                self.photo_id = upload_photo(image)


class Category(PaginatedAPIMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.String(512))
    photo_id = db.Column(db.String(128))
    items = db.relationship('Item', backref='category', lazy='dynamic')

    def __repr__(self):
        return '<name:{} \n id:{}> \n photo_id:{}>'.format(self.name, self.id, self.photo_id)

    def get_items(self):
        return Item.query.filter_by(category_id=self.id)

    def to_dict(self, to_collection=False):
        thumbnail_size = 500
        if to_collection:
            thumbnail_size = 120
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'items_count': self.get_items().count(),
            'photo_data': self.get_thumbnail(self.photo_id, thumbnail_size, url=False),
            '_links': {
                'self': url_for('api.get_category', id=self.id),
                'collection of categories': url_for('api.get_categories')
            }
        }
        return data

    def from_dict(self, data):
        for field in ['name', 'description']:
            if field in data:
                setattr(self, field, data[field])
            if 'photo_data' in data:
                image = base64.b64decode(data['photo_data'])
                self.photo_id = upload_photo(image)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))