"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


# import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

# os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app
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


class UserModelTestCase(TestCase):
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


    def test_user_model(self):
        """Does basic USER model work?"""

        with app.app_context():
            u = User(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD"
            )

            db.session.add(u)
            db.session.commit()

            # User should have no messages & no followers
            self.assertEqual(len(u.messages), 0)
            self.assertEqual(len(u.followers), 0)
            

    def test_is_followed_by(self):
        with app.app_context():
            user1 = User.query.get_or_404(self.user1_id)
            user2 = User.query.get_or_404(self.user2_id)
            
            user1.following.append(user2)
            db.session.commit()

            self.assertTrue(user2.is_followed_by(user1))
            self.assertFalse(user1.is_followed_by(user2))


    def test_is_following(self):
        with app.app_context():
            user1 = User.query.get_or_404(self.user1_id)
            user2 = User.query.get_or_404(self.user2_id)
            
            user1.following.append(user2)
            db.session.commit()

            self.assertTrue(user1.is_following(user2))
            self.assertFalse(user2.is_following(user1))


    # USER Signup Tests
    def test_valid_signup(self):
        with app.app_context():
            user = User.signup(
                "testuser", "test@test.com", "HASHED_PASSWORD", None)
            db.session.commit()

            self.assertEqual(user.username, "testuser")
            self.assertEqual(user.email, "test@test.com")
            self.assertNotEqual(user.password, "HASHED_PASSWORD")
            # Bcrypt strings should start with $2b$
            self.assertTrue(user.password.startswith("$2b$"))

    def test_invalid_username_signup(self):
        with app.app_context():
            invalid = User.signup(None, "test@test.com", "HASHED_PASSWORD", None)
            with self.assertRaises(exc.IntegrityError) as context:
                db.session.commit()

    def test_invalid_email_signup(self):
        with app.app_context():
            invalid = User.signup("testuser", None, "HASHED_PASSWORD", None)
            with self.assertRaises(exc.IntegrityError) as context:
                db.session.commit()

    def test_invalid_password_signup(self):
        with app.app_context():
            with self.assertRaises(ValueError) as context:
                User.signup("testuser", "test@test.com", "", None)

            with self.assertRaises(ValueError) as context:
                User.signup("testuser", "test@test.com", None, None)
                
                
    # USER Authentication Tests ####################################
    def test_valid_authentication(self):
        with app.app_context():
            user1 = User.query.get_or_404(self.user1_id)
            
            user = User.authenticate(user1.username, "HASHED_PASSWORD")
            self.assertIsNotNone(user)
            self.assertEqual(user.id, user1.id)

    def test_wrong_username(self):
        with app.app_context():
            self.assertFalse(User.authenticate("wrong_username", "HASHED_PASSWORD"))

    def test_wrong_password(self):
        with app.app_context():
            user1 = User.query.get_or_404(self.user1_id)
            self.assertFalse(User.authenticate(user1.username, "wrong_password"))
                
                
    # check user password method ####################################
    def test_check_password(self):
        with app.app_context():
            user = User.query.get_or_404(self.user1_id)
            self.assertTrue(User.check_password(user.username, "HASHED_PASSWORD"))            
            self.assertFalse(User.check_password(user.username, "wrong_password"))