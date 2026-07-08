from models import db
from datetime import datetime


class Pembayaran(db.Model):
    __tablename__ = "pembayaran"

    id_pembayaran = db.Column(db.Integer, primary_key=True)
    metode = db.Column(db.Enum("Cash", "QRIS"), nullable=False)
    jumlah_bayar = db.Column(db.Numeric(10, 2), nullable=False)
    tanggal_bayar = db.Column(db.DateTime, default=datetime.now, nullable=True)
    transaksi_id_transaksi = db.Column(db.Integer, db.ForeignKey("transaksi.id_transaksi", ondelete="CASCADE"), nullable=False)
    transaksi = db.relationship(
        "Transaksi",
        foreign_keys=[transaksi_id_transaksi],
        back_populates="pembayaran",
        passive_deletes=True,
    )

    def format_jumlah(self):
        """Format amount as Indonesian currency"""
        return f"Rp {float(self.jumlah_bayar):,.0f}".replace(",", ".")
