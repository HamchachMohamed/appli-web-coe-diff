from . import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    reset_token = db.Column(db.String(100), unique=True, nullable=True, default=None)
    reset_code = db.Column(db.String(6), nullable=True)
    reset_code_timestamp = db.Column(db.DateTime, nullable=True)
    
    def __init__(self, email, first_name, password):
        self.email = email
        self.first_name = first_name
        self.password = password
        self.reset_token = None