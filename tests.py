#!/usr/bin/env python
import unittest
from app import create_app, db
from app.models import User, Item, Category
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'


class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(username='susan')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    def test_group_get_items(self):
        category = Category(name='TEST CATEGORY NAME')
        item1 = Item(title='TEST ITEM NAME 1', group_id=1)
        item2 = Item(title='TEST ITEM NAME 2', group_id=1)
        db.session.add(category)
        db.session.add(item1)
        db.session.add(item2)
        db.session.commit()
        self.assertTrue(item1 in category.get_items().all())
        self.assertTrue(item2 in category.get_items().all())


if __name__ == '__main__':
    unittest.main(verbosity=2)
