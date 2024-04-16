"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


# import os
from unittest import TestCase

from models import db, connect_db, Message, User, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

# os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///warbler-test'
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

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        with app.app_context():
            User.query.delete()
            Message.query.delete()
            Follows.query.delete()
            Likes.query.delete()

            user1 = User.signup(username="testuser1",
                                        email="test1@test.com",
                                        password="HASHED_PASSWORD",
                                        image_url=None)

            db.session.add(user1)
            db.session.commit()
            
            self.user1_id = user1.id
        
        self.client = app.test_client()

    def tearDown(self):
        """Clean up fouled transactions."""
        with app.app_context():
            db.session.rollback()    


    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with app.app_context():
            user = User.query.get_or_404(self.user1_id)
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = user.id

                # Now, that session setting is saved, so we can have
                # the rest of ours test

                resp = c.post("/messages/new", data={"text": "Hello"})

                # Make sure it redirects
                self.assertEqual(resp.status_code, 302)

                msg = Message.query.one()
                self.assertEqual(msg.text, "Hello")
