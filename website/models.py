from . import db
from flask_login import UserMixin


class ArtLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    location_name = db.Column(db.String(64))
    location_type = db.Column(db.String(64))
    address = db.Column(db.String(64))
    description = db.Column(db.String(1024))
    location_image = db.Column(db.LargeBinary)


class Review(db.Model):
    review_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    location_id = db.Column(db.Integer, db.ForeignKey('art_location.id'))
    stars = db.Column(db.Float())
    comment = db.Column(db.String(1024))
    review_image = db.Column(db.LargeBinary)
    upvote = db.Column(db.Integer())
    downvote = db.Column(db.Integer())

    def __init__(self, stars, comment, review_image, user_id):
        self.stars = stars
        self.comment = comment
        self.review_image = review_image
        self.user_id = user_id

class User(db.Model, UserMixin):
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(512))
    displayName = db.Column(db.String(10), unique=True)
    reviews = db.relationship('Review')

    def get_id(self):
        return str(self.user_id)