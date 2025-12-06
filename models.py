from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200))
    google_id = db.Column(db.String(200))
    name = db.Column(db.String(120))
    analyses = db.relationship("Analysis", backref="user", lazy=True)

class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    repo_name = db.Column(db.String(200))
    score = db.Column(db.Float)
    pdf_path = db.Column(db.String(300))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
