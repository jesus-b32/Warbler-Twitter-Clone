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


class UserViewTestCase(TestCase):
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
            user2 = User.signup(username="testuser2",
                                        email="test2@test.com",
                                        password="HASHED_PASSWORD",
                                        image_url=None)
            user3 = User.signup(username="user3",
                                        email="user3@user.com",
                                        password="HASHED_PASSWORD",
                                        image_url=None)
            user4 = User.signup(username="user4",
                                        email="user4@user.com",
                                        password="HASHED_PASSWORD",
                                        image_url=None)

            db.session.commit()
            
            self.user1_id = user1.id
            self.user2_id = user2.id
            self.user3_id = user3.id
            self.user4_id = user4.id
        
        self.client = app.test_client()

    def tearDown(self):
        """Clean up fouled transactions."""
        with app.app_context():
            db.session.rollback()    


    def test_list_users(self):
        """Can use add a message?"""
        with self.client as c:
            resp = c.get("/users")

            self.assertIn("@testuser1", str(resp.data))
            self.assertIn("@testuser2", str(resp.data))
            
            
    def test_users_search(self):
        with self.client as c:
            resp = c.get("/users?q=test")

            self.assertIn("@testuser1", str(resp.data))
            self.assertIn("@testuser2", str(resp.data))
            self.assertNotIn("@user3", str(resp.data)) 
            

    def test_user_show(self):
        with self.client as c:
            resp = c.get(f"/users/{self.user1_id}")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser1", str(resp.data))   
            
            
    def setup_followers(self):
        with app.app_context():
            f1 = Follows(user_being_followed_id=self.user1_id,
                        user_following_id=self.user3_id)
            f2 = Follows(user_being_followed_id=self.user2_id,
                        user_following_id=self.user3_id)
            f3 = Follows(user_being_followed_id=self.user3_id,
                        user_following_id=self.user1_id)

            db.session.add_all([f1, f2, f3])
            db.session.commit()
        
        
    def test_show_following(self):
        """Test that this Show list of people this user is following.
        """
        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user3_id

            resp = c.get(f"/users/{self.user3_id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser1", str(resp.data))
            self.assertIn("@testuser2", str(resp.data))
            self.assertNotIn("@user4", str(resp.data)) 
            
            
    def test_show_followers(self):
        """Test that this Show list of followers of this user.
        """
        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user3_id

            resp = c.get(f"/users/{self.user3_id}/followers")

            self.assertIn("@testuser1", str(resp.data))
            self.assertNotIn("@user2_id", str(resp.data))
            self.assertNotIn("@testuser2", str(resp.data))
            self.assertNotIn("@user4", str(resp.data))
            
            
    def test_unauthorized_following_page_access(self):
        self.setup_followers()
        with self.client as c:
            resp = c.get(
                f"/users/{self.user3_id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@testuser1", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))

    def test_unauthorized_followers_page_access(self):
        self.setup_followers()
        with self.client as c:
            resp = c.get(
                f"/users/{self.user3_id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@testuser1", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))         
            
            
    def test_add_follow(self):
        """Test that user1 is added to user3 following list.
        """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user3_id

            resp = c.post(f"/users/follow/{self.user1_id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser1", str(resp.data))
            self.assertNotIn("@testuser2", str(resp.data))
            self.assertNotIn("@user4", str(resp.data))    
            
            
    def test_stop_following(self):
        """Test that user2 is removed from user3 following list while user2 remains in list.
        """
        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user3_id

            resp = c.post(f"/users/stop-following/{self.user2_id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser1", str(resp.data))
            self.assertNotIn("@testuser2", str(resp.data))
            self.assertNotIn("@user4", str(resp.data))  


    def setup_likes(self):
        with app.app_context():
            message = Message(id=1234, text="I like this", user_id=self.user1_id)
            db.session.add(message)
            db.session.commit()

            l1 = Likes(user_id=self.user3_id, message_id=1234)
            db.session.add(l1)
            db.session.commit()        


    def test_register_user_like(self):
        with app.app_context():
            message = Message(text="Test test 123.", user_id=self.user1_id)
            db.session.add(message)
            db.session.commit()

            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.user3_id

                resp = c.post(f"/users/add_like/{message.id}", follow_redirects=True)
                self.assertEqual(resp.status_code, 200)

                likes = Likes.query.filter(Likes.message_id == message.id).all()
                self.assertEqual(len(likes), 1)
                self.assertEqual(likes[0].user_id, self.user3_id)


    def test_register_user_unlike(self):
        """Test if currently liked message by users 3 gets unliked
        """
        self.setup_likes()
            
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user3_id

            resp = c.post("/users/add_like/1234", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id == 1234).all()
            self.assertEqual(len(likes), 0)


    def test_unauthenticated_like(self):
        self.setup_likes()

        with self.client as c:
            resp = c.post("/users/add_like/1234", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn("Access unauthorized", str(resp.data))




    def test_show_likes(self):
        self.setup_likes()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user3_id

            resp = c.get(f"/users/{self.user3_id}/likes", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn("@user3", str(resp.data))
            self.assertIn("I like this", str(resp.data))
            
            
    def test_unauthenticated_show_like(self):
        self.setup_likes()

        with self.client as c:
            resp = c.get(f"/users/{self.user3_id}/likes", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn("Access unauthorized", str(resp.data))