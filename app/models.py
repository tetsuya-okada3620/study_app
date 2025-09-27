from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from flask_login import UserMixin
from app.extensions import db
import datetime

class Guest(UserMixin):
    def __init__(self):
        self.id = "Guest"
        self.name = "Guest"
        self.is_guest = True

class Records(db.Model):
    __tablename__ = "records"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(20), ForeignKey("users.user_id"))
    confirm = db.Column(db.Text)
    study_date_start = db.Column(db.DateTime)
    study_date_end = db.Column(db.DateTime)
    write_date = db.Column(db.DateTime)
    remark = db.Column(db.Text)
    category_id = db.Column(db.Integer, ForeignKey("categories.category_id"))

    @hybrid_property
    def study_duration(self):
        return int((self.study_date_end - self.study_date_start).total_seconds()) // 60

class Users(db.Model, UserMixin):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text)
    password = db.Column(db.Text)

    def get_id(self):
        return str(self.user_id)

    records = db.relationship("Records", backref="users")

class Categories(db.Model):
    __tablename__ = "categories"
    category_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_name = db.Column(db.String(30))

    records = db.relationship("Records", backref="categories")

class Foot(db.Model):
    __tablename__ = "foot"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hash = db.Column(db.Text)
    foot_date = db.Column(db.Date, default=datetime.date.today)  # PG側で現在の日付をデフォルト値とする。