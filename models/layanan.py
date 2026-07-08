from models import db


class Layanan(db.Model):
    __tablename__ = "layanan"

    id_layanan = db.Column(db.Integer, primary_key=True)
    nama_layanan = db.Column(db.String(100), nullable=False)
    harga_perkg = db.Column(db.Numeric(10, 2), nullable=False)
    estimasi_hari = db.Column(db.Integer, nullable=False)
    detail_transaksi = db.relationship(
        "DetailTransaksi",
        back_populates="layanan",
        foreign_keys="DetailTransaksi.layanan_id_layanan",
        lazy="dynamic",
        passive_deletes=True,
    )

    def harga_rupiah(self):
        return f"Rp {float(self.harga_perkg):,.0f}".replace(",", ".")
