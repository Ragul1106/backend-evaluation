from . import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class Applicant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False, index=True)
    phone = db.Column(db.String(30), nullable=True)
    dob = db.Column(db.Date, nullable=True)
    course = db.Column(db.String(100))
    address = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    applied_on = db.Column(db.DateTime, default=datetime.utcnow)
    admin_comment = db.Column(db.Text)

    def __repr__(self):
        return f'<Applicant {self.id} {self.full_name}>'

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
