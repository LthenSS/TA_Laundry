from datetime import datetime

from models import db


class Pelanggan(db.Model):
    __tablename__ = "pelanggan"

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    no_hp = db.Column(db.String(20), nullable=True)
    alamat = db.Column(db.Text, nullable=True)
    is_member = db.Column(db.Boolean, default=False, nullable=True)
    total_point = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=True)
    transaksi = db.relationship("Transaksi", back_populates="pelanggan", foreign_keys="Transaksi.pelanggan_id", lazy="dynamic")
    point_history = db.relationship("PointMember", back_populates="pelanggan", foreign_keys="PointMember.pelanggan_id", lazy="dynamic")

    @property
    def jenis_pelanggan(self):
        return "Member" if self.is_member else "Non Member"

    def format_tanggal(self):
        """Format tanggal dalam format Indonesia"""
        return self.created_at.strftime("%d/%m/%Y %H:%M")

    def jenis_label(self):
        return self.jenis_pelanggan or "Member"
