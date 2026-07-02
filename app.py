from flask import Flask
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


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    print("CONFIG FROM APP:", app.config.get("WHATSAPP_API_KEY"))

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

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
