from datetime import datetime

from models import db


class Transaksi(db.Model):
    __tablename__ = "transaksi"

    id_transaksi = db.Column(db.Integer, primary_key=True)
    kode_transaksi = db.Column(db.String(30), nullable=False)
    tanggal = db.Column(db.DateTime, default=datetime.now, nullable=True)
    subtotal = db.Column(db.Numeric(10, 2), default=0, nullable=True)
    diskon = db.Column(db.Numeric(10, 2), default=0, nullable=True)
    total = db.Column(db.Numeric(10, 2), default=0, nullable=True)
    status_laundry = db.Column(
        db.Enum("Antrian", "Diproses", "Siap Diambil", "Selesai"),
        default="Antrian",
        nullable=True
    )
    status_pembayaran = db.Column(
        db.Enum("Belum Bayar", "Lunas"),
        default="Belum Bayar",
        nullable=True
    )
    users_id_users = db.Column(db.Integer, db.ForeignKey("users.id_users"), nullable=False)
    promo_id_promo = db.Column(db.Integer, db.ForeignKey("promo.id_promo"), nullable=True)
    pelanggan_id = db.Column(db.Integer, db.ForeignKey("pelanggan.id"), nullable=True)
    catatan = db.Column(db.Text, nullable=True)
    pelanggan = db.relationship("Pelanggan", foreign_keys=[pelanggan_id], back_populates="transaksi")
    user = db.relationship("User", foreign_keys=[users_id_users])
    promo = db.relationship("Promo", foreign_keys=[promo_id_promo])
    detail_transaksi = db.relationship("DetailTransaksi", back_populates="transaksi", foreign_keys="DetailTransaksi.transaksi_id_transaksi", lazy="dynamic")
    pembayaran = db.relationship("Pembayaran", back_populates="transaksi", foreign_keys="Pembayaran.transaksi_id_transaksi", uselist=False)
    point_history = db.relationship("PointMember", back_populates="transaksi", foreign_keys="PointMember.transaksi_id_transaksi", lazy="dynamic")

    def format_id(self):
        """Format transaction ID"""
        return self.kode_transaksi

    def format_status_badge(self):
        """Get status badge class"""
        status_map = {
            "Antrian": "queue",
            "Diproses": "wash",
            "Siap Diambil": "ready",
            "Selesai": "done",
        }
        return status_map.get(self.status_laundry, "queue")
