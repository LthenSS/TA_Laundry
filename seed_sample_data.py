from datetime import datetime, timedelta
from decimal import Decimal

from flask import Flask
from werkzeug.security import generate_password_hash

from config import Config
from models import db
from models.layanan import Layanan
from models.promo import Promo
from models.user import User
from models.member import Pelanggan
from models.transaksi import Transaksi
from models.detail_transaksi import DetailTransaksi
from models.pembayaran import Pembayaran
from models.point_member import PointMember


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app


def get_or_create(model, defaults=None, **kwargs):
    instance = model.query.filter_by(**kwargs).first()
    if instance:
        return instance, False
    params = dict(kwargs)
    if defaults:
        params.update(defaults)
    instance = model(**params)
    db.session.add(instance)
    db.session.flush()
    return instance, True


def seed_data(app=None):
    if app is None:
        app = create_app()
    with app.app_context():
        db.create_all()

        print("Seeding sample data...")

        layanan_data = [
            {"nama_layanan": "Cuci Komplit (3kg)", "harga_perkg": Decimal("12000"), "estimasi_hari": 1},
            {"nama_layanan": "Cuci Kering (2kg)", "harga_perkg": Decimal("10000"), "estimasi_hari": 1},
            {"nama_layanan": "Setrika Saja (5kg)", "harga_perkg": Decimal("9000"), "estimasi_hari": 1},
            {"nama_layanan": "Cuci + Setrika (4kg)", "harga_perkg": Decimal("14000"), "estimasi_hari": 2},
            {"nama_layanan": "Pewangi Ekstra", "harga_perkg": Decimal("5000"), "estimasi_hari": 1},
        ]
        for service in layanan_data:
            obj, created = get_or_create(Layanan, **service)
            if created:
                print(f"  - Added layanan: {obj.nama_layanan}")

        promo_data = [
            {
                "nama_promo": "Diskon 10% untuk Transaksi >= 100K",
                "tipe_diskon": "Persen",
                "nilai_diskon": Decimal("10"),
                "minimal_transaksi": Decimal("100000"),
                "status": "Aktif",
            },
            {
                "nama_promo": "Potongan 15K untuk >= 75K",
                "tipe_diskon": "Nominal",
                "nilai_diskon": Decimal("15000"),
                "minimal_transaksi": Decimal("75000"),
                "status": "Aktif",
            },
            {
                "nama_promo": "Promo Lama 20%",
                "tipe_diskon": "Persen",
                "nilai_diskon": Decimal("20"),
                "minimal_transaksi": Decimal("150000"),
                "status": "Tidak Aktif",
            },
        ]
        for promo in promo_data:
            obj, created = get_or_create(Promo, **promo)
            if created:
                print(f"  - Added promo: {obj.nama_promo}")

        employees = [
            {"nama": "Rini", "username": "kasir1", "password": generate_password_hash("kasir123"), "role": "Karyawan"},
            {"nama": "Bayu", "username": "kasir2", "password": generate_password_hash("kasir123"), "role": "Karyawan"},
            {"nama": "Dewi", "username": "kasir3", "password": generate_password_hash("kasir123"), "role": "Karyawan"},
        ]
        for emp in employees:
            obj, created = get_or_create(User, defaults={"password": emp["password"], "role": emp["role"]}, username=emp["username"], nama=emp["nama"])
            if created:
                print(f"  - Added karyawan: {obj.username}")

        pelanggan_data = [
            {"nama": "Anton", "no_hp": "081234567890", "alamat": "Jl. Melati No. 12", "is_member": True, "total_point": 120},
            {"nama": "Siti", "no_hp": "081298765432", "alamat": "Jl. Kenanga No. 5", "is_member": True, "total_point": 80},
            {"nama": "Dimas", "no_hp": "082112345678", "alamat": "Perum Bumi Asri", "is_member": False, "total_point": 0},
            {"nama": "Eni", "no_hp": "082134567890", "alamat": "Komplek Merpati", "is_member": False, "total_point": 0},
            {"nama": "Rina", "no_hp": "081355667788", "alamat": "Jl. Anggrek No. 21", "is_member": True, "total_point": 45},
            {"nama": "Mira", "no_hp": "081223344556", "alamat": "Jl. Dahlia No. 7", "is_member": True, "total_point": 30},
            {"nama": "Budi", "no_hp": "085667788990", "alamat": "Perumahan Sinar Baru", "is_member": False, "total_point": 0},
            {"nama": "Tono", "no_hp": "082176543210", "alamat": "Jl. Bougenville No. 9", "is_member": True, "total_point": 15},
        ]
        for customer in pelanggan_data:
            obj, created = get_or_create(Pelanggan, **customer)
            if created:
                print(f"  - Added pelanggan: {obj.nama} ({'Member' if obj.is_member else 'Non-member'})")

        layanan_map = {layanan.nama_layanan: layanan for layanan in Layanan.query.all()}
        promo_map = {promo.nama_promo: promo for promo in Promo.query.all()}
        user_map = {user.username: user for user in User.query.filter(User.role == "Karyawan").all()}
        pelanggan_map = {pelanggan.nama: pelanggan for pelanggan in Pelanggan.query.all()}

        transaksi_samples = [
            {
                "kode_transaksi": "TRX-20260618-001",
                "tanggal": datetime.now() - timedelta(days=20),
                "pelanggan": pelanggan_map["Anton"],
                "karyawan": user_map["kasir1"],
                "promo": promo_map["Diskon 10% untuk Transaksi >= 100K"],
                "items": [
                    {"layanan": layanan_map["Cuci Komplit (3kg)"], "berat": Decimal("3")},
                    {"layanan": layanan_map["Pewangi Ekstra"], "berat": Decimal("1")},
                ],
                "status_laundry": "Selesai",
                "status_pembayaran": "Lunas",
                "catatan": "Ambil esok hari",
                "pembayaran_metode": "Cash",
                "point_earned": 20,
            },
            {
                "kode_transaksi": "TRX-20260622-002",
                "tanggal": datetime.now() - timedelta(days=16),
                "pelanggan": pelanggan_map["Siti"],
                "karyawan": user_map["kasir2"],
                "promo": promo_map["Potongan 15K untuk >= 75K"],
                "items": [
                    {"layanan": layanan_map["Setrika Saja (5kg)"], "berat": Decimal("5")},
                ],
                "status_laundry": "Diproses",
                "status_pembayaran": "Lunas",
                "catatan": "Mau cepat selesai",
                "pembayaran_metode": "QRIS",
                "point_earned": 10,
            },
            {
                "kode_transaksi": "TRX-20260625-003",
                "tanggal": datetime.now() - timedelta(days=13),
                "pelanggan": pelanggan_map["Dimas"],
                "karyawan": user_map["kasir1"],
                "promo": None,
                "items": [
                    {"layanan": layanan_map["Cuci Kering (2kg)"], "berat": Decimal("2")},
                    {"layanan": layanan_map["Cuci Komplit (3kg)"], "berat": Decimal("3")},
                ],
                "status_laundry": "Siap Diambil",
                "status_pembayaran": "Belum Bayar",
                "catatan": "Tunggu sms pembayaran",
                "pembayaran_metode": None,
                "point_earned": 0,
            },
            {
                "kode_transaksi": "TRX-20260701-004",
                "tanggal": datetime.now() - timedelta(days=7),
                "pelanggan": pelanggan_map["Eni"],
                "karyawan": user_map["kasir2"],
                "promo": promo_map["Diskon 10% untuk Transaksi >= 100K"],
                "items": [
                    {"layanan": layanan_map["Cuci + Setrika (4kg)"], "berat": Decimal("4")},
                ],
                "status_laundry": "Selesai",
                "status_pembayaran": "Lunas",
                "catatan": "Butuh setrika ekstra",
                "pembayaran_metode": "Cash",
                "point_earned": 0,
            },
            {
                "kode_transaksi": "TRX-20260703-005",
                "tanggal": datetime.now() - timedelta(days=5),
                "pelanggan": pelanggan_map["Rina"],
                "karyawan": user_map["kasir1"],
                "promo": promo_map["Potongan 15K untuk >= 75K"],
                "items": [
                    {"layanan": layanan_map["Cuci Komplit (3kg)"], "berat": Decimal("3")},
                ],
                "status_laundry": "Antrian",
                "status_pembayaran": "Belum Bayar",
                "catatan": "Hanya cuci komplit",
                "pembayaran_metode": None,
                "point_earned": 5,
            },
            {
                "kode_transaksi": "TRX-20260705-006",
                "tanggal": datetime.now() - timedelta(days=3),
                "pelanggan": pelanggan_map["Anton"],
                "karyawan": user_map["kasir2"],
                "promo": None,
                "items": [
                    {"layanan": layanan_map["Setrika Saja (5kg)"], "berat": Decimal("3")},
                ],
                "status_laundry": "Diproses",
                "status_pembayaran": "Lunas",
                "catatan": "Pakai setrika halus",
                "pembayaran_metode": "QRIS",
                "point_earned": 12,
            },
        ]

        for sample in transaksi_samples:
            transaksi = Transaksi.query.filter_by(kode_transaksi=sample["kode_transaksi"]).first()
            if transaksi:
                print(f"  - Transaksi sudah ada: {sample['kode_transaksi']}")
                continue

            subtotal = Decimal(0)
            for item in sample["items"]:
                subtotal += item["layanan"].harga_perkg * item["berat"]

            diskon = Decimal(0)
            if sample["promo"] and subtotal >= sample["promo"].minimal_transaksi:
                if sample["promo"].tipe_diskon == "Persen":
                    diskon = (subtotal * sample["promo"].nilai_diskon) / Decimal(100)
                else:
                    diskon = sample["promo"].nilai_diskon

            total = subtotal - diskon
            total = total.quantize(Decimal("1."))

            transaksi = Transaksi(
                kode_transaksi=sample["kode_transaksi"],
                tanggal=sample["tanggal"],
                pelanggan_id=sample["pelanggan"].id,
                users_id_users=sample["karyawan"].id_users,
                promo_id_promo=sample["promo"].id_promo if sample["promo"] else None,
                subtotal=subtotal,
                diskon=diskon,
                total=total,
                status_laundry=sample["status_laundry"],
                status_pembayaran=sample["status_pembayaran"],
                catatan=sample["catatan"],
            )
            db.session.add(transaksi)
            db.session.flush()

            for item in sample["items"]:
                detail = DetailTransaksi(
                    berat=item["berat"],
                    harga=item["layanan"].harga_perkg,
                    sub_total=item["layanan"].harga_perkg * item["berat"],
                    transaksi_id_transaksi=transaksi.id_transaksi,
                    layanan_id_layanan=item["layanan"].id_layanan,
                )
                db.session.add(detail)

            if sample["status_pembayaran"] == "Lunas":
                pembayaran = Pembayaran(
                    metode=sample["pembayaran_metode"],
                    jumlah_bayar=total,
                    tanggal_bayar=sample["tanggal"] + timedelta(hours=1),
                    transaksi_id_transaksi=transaksi.id_transaksi,
                )
                db.session.add(pembayaran)

            if sample["pelanggan"].is_member and sample["point_earned"]:
                point = PointMember(
                    point_masuk=sample["point_earned"],
                    point_keluar=0,
                    keterangan=f"Transaksi {sample['kode_transaksi']}",
                    tanggal=sample["tanggal"],
                    pelanggan_id=sample["pelanggan"].id,
                    transaksi_id_transaksi=transaksi.id_transaksi,
                )
                db.session.add(point)
                sample["pelanggan"].total_point += sample["point_earned"]

            print(f"  - Added transaksi: {sample['kode_transaksi']} (total Rp {total:,})")

        db.session.commit()
        print("Seed selesai.")


if __name__ == "__main__":
    seed_data()
