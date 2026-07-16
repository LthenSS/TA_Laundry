from models import db


class Promo(db.Model):
    __tablename__ = "promo"

    id_promo = db.Column(db.Integer, primary_key=True)
    nama_promo = db.Column(db.String(100), nullable=False)
    tipe_diskon = db.Column(db.Enum("Persen", "Nominal"), nullable=False)
    nilai_diskon = db.Column(db.Numeric(10, 2), nullable=False)
    minimal_transaksi = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum("Aktif", "Tidak Aktif"), default="Aktif")
    tanggal_mulai = db.Column(db.Date, nullable=True)
    tanggal_selesai = db.Column(db.Date, nullable=True)

    def nilai_label(self):
        if self.tipe_diskon == "Persen":
            return f"{float(self.nilai_diskon):.0f}%"
        return f"-Rp {float(self.nilai_diskon):,.0f}".replace(",", ".")

    def minimal_label(self):
        return f">= Rp {float(self.minimal_transaksi):,.0f}".replace(",", ".")
