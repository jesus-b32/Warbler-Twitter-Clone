"""Seed database with sample data from CSV Files."""

from csv import DictReader
from app import db, app
from models import User, Message, Follows

with app.app_context():
    db.drop_all()
    db.create_all()

with open('generator/users.csv') as users:
    with app.app_context():
        db.session.bulk_insert_mappings(User, DictReader(users))
        db.session.commit()

with open('generator/messages.csv') as messages:
    with app.app_context():
        db.session.bulk_insert_mappings(Message, DictReader(messages))
        db.session.commit()

with open('generator/follows.csv') as follows:
    with app.app_context():
        db.session.bulk_insert_mappings(Follows, DictReader(follows))
        db.session.commit()

# with app.app_context():
#     db.session.commit()
