from datetime import datetime

from models import db


class PointMember(db.Model):
    __tablename__ = "point_member"

    id_point = db.Column(db.Integer, primary_key=True)
    point_masuk = db.Column(db.Integer, default=0, nullable=True)
    point_keluar = db.Column(db.Integer, default=0, nullable=True)
    keterangan = db.Column(db.String(255), nullable=True)
    tanggal = db.Column(db.DateTime, default=datetime.now, nullable=False)
    pelanggan_id = db.Column(db.Integer, db.ForeignKey("pelanggan.id"), nullable=False)
    transaksi_id_transaksi = db.Column(db.Integer, db.ForeignKey("transaksi.id_transaksi"), nullable=False)
    pelanggan = db.relationship("Pelanggan", foreign_keys=[pelanggan_id], back_populates="point_history")
    transaksi = db.relationship("Transaksi", foreign_keys=[transaksi_id_transaksi], back_populates="point_history")
