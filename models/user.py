from models import db


class User(db.Model):
    __tablename__ = "users"

    id_users = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("Owner", "Karyawan"), nullable=False)
