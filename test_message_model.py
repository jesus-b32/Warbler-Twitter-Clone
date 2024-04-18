"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///warbler-test'
app.config['SQLALCHEMY_ECHO'] = False
app.config['TESTING'] = True

# This is a bit of hack, but don't use Flask DebugToolbar
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

with app.app_context():
    db.drop_all()
    db.create_all()


class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        with app.app_context():
            
            User.query.delete()
            Message.query.delete()
            Follows.query.delete()
            Likes.query.delete()

            user1 = User.signup("testuser1", "test1@test.com", "HASHED_PASSWORD", None)

            user2 = User.signup("testuser2", "test2@test.com", "HASHED_PASSWORD", None)

            db.session.commit()
            
            self.user1_id = user1.id        
            self.user2_id = user2.id        


        self.client = app.test_client()

    def tearDown(self):
        """Clean up fouled transactions."""
        with app.app_context():
            db.session.rollback()    


    def test_message_model(self):
        """Does basic MESSAGE model work?"""

        with app.app_context():
            user = User.query.get_or_404(self.user1_id)
            message = Message(
                text="Testing Message Model!",
                user_id=user.id)

            db.session.add(message)
            db.session.commit()

            # User should have no messages & no followers
            self.assertEqual(len(user.messages), 1)
            self.assertEqual(user.messages[0].text, "Testing Message Model!")
            self.assertEqual(user.messages[0].user_id, self.user1_id)

    def test_message_is_liked(self):
        """Testing Message is liked method"""

        with app.app_context():
            user1 = User.query.get_or_404(self.user1_id)
            
            message = Message(
                text="Testing Message Model!",
                user_id=user1.id
            )

            user2 = User.query.get_or_404(self.user2_id)
            user2.likes.append(message)
            db.session.commit()
            
            self.assertTrue(message.is_liked(user2))
            self.assertFalse(message.is_liked(user1))