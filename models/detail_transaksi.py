from models import db


class DetailTransaksi(db.Model):
    __tablename__ = "detail_transaksi"

    id_detail = db.Column(db.Integer, primary_key=True)
    berat = db.Column(db.Numeric(5, 2), nullable=False)
    harga = db.Column(db.Numeric(10, 2), nullable=False)
    sub_total = db.Column(db.Numeric(10, 2), nullable=False)
    transaksi_id_transaksi = db.Column(db.Integer, db.ForeignKey("transaksi.id_transaksi", ondelete="CASCADE"), nullable=False)
    layanan_id_layanan = db.Column(db.Integer, db.ForeignKey("layanan.id_layanan", ondelete="CASCADE"), nullable=False)
    transaksi = db.relationship(
        "Transaksi",
        foreign_keys=[transaksi_id_transaksi],
        back_populates="detail_transaksi",
        passive_deletes=True,
    )
    layanan = db.relationship(
        "Layanan",
        foreign_keys=[layanan_id_layanan],
        back_populates="detail_transaksi",
        passive_deletes=True,
    )

    def format_subtotal(self):
        """Format subtotal as Indonesian currency"""
        return f"Rp {float(self.sub_total):,.0f}".replace(",", ".")
