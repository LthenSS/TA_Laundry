import os
import sys
from urllib.parse import urlsplit, urlunsplit

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from flask import Flask
from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash

from config import Config
from models import db
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.karyawan import karyawan_bp
from routes.kasir import kasir_bp
from routes.laporan import laporan_bp
from routes.layanan import layanan_bp
from routes.member import member_bp
from routes.promo import promo_bp
from routes.transaksi import transaksi_bp


def ensure_database_exists(app):
    database_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
    if not database_uri:
        return

    parsed = urlsplit(database_uri)
    if parsed.scheme.startswith("sqlite"):
        return

    database_name = parsed.path.lstrip("/")
    if not database_name:
        return

    admin_uri = urlunsplit((parsed.scheme, parsed.netloc, "", parsed.query, parsed.fragment))
    try:
        engine = create_engine(admin_uri, isolation_level="AUTOCOMMIT")
        with engine.connect() as connection:
            connection.execute(text(f"CREATE DATABASE IF NOT EXISTS `{database_name}`"))
        engine.dispose()
    except Exception as exc:
        print(f"Unable to ensure database exists: {exc}")


def seed_default_user(app):
    with app.app_context():
        from models.user import User

        if User.query.filter_by(username="owner").first() is None:
            owner_user = User(
                nama="Owner",
                username="owner",
                password=generate_password_hash("owner123"),
                role="Owner",
            )
            db.session.add(owner_user)
            db.session.commit()

        if User.query.filter_by(username="kasir").first() is None:
            kasir_user = User(
                nama="Kasir",
                username="kasir",
                password=generate_password_hash("kasir123"),
                role="Karyawan",
            )
            db.session.add(kasir_user)
            db.session.commit()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    print("CONFIG FROM APP:", app.config.get("WHATSAPP_API_KEY"))

    ensure_database_exists(app)
    db.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(kasir_bp)
    app.register_blueprint(laporan_bp)
    app.register_blueprint(layanan_bp)
    app.register_blueprint(karyawan_bp)
    app.register_blueprint(member_bp)
    app.register_blueprint(promo_bp)
    app.register_blueprint(transaksi_bp)

    with app.app_context():
        db.create_all()
        seed_default_user(app)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
