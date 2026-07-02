from datetime import datetime

MODEL_STATUS_TO_UI = {
    "Antrian": "Antrian",
    "Diproses": "Diproses",
    "Siap Diambil": "Siap Diambil",
    "Selesai": "Selesai",
}

UI_STATUS_TO_MODEL = {value: key for key, value in MODEL_STATUS_TO_UI.items()}


def _alias_attrs(obj, aliases):
    if obj is None:
        return None

    for alias_name, provider in aliases.items():
        if not hasattr(obj, alias_name):
            value = provider(obj) if callable(provider) else provider
            setattr(obj, alias_name, value)

    return obj


def alias_member(member):
    return _alias_attrs(member, {
        "id_member": lambda m: m.id,
        "create_at": lambda m: m.created_at,
    })


def alias_members(members):
    return [alias_member(member) for member in members]


def alias_detail(detail):
    return _alias_attrs(detail, {
        "harga_satuan": lambda d: d.harga,
        "subtotal": lambda d: d.sub_total,
        "layanan_id": lambda d: d.layanan_id_layanan,
    })


def alias_details(details):
    return [alias_detail(detail) for detail in details]


def alias_payment(pembayaran):
    if pembayaran is None:
        return None

    transaksi = getattr(pembayaran, "transaksi", None)
    return _alias_attrs(pembayaran, {
        "metode_pembayaran": lambda p: p.metode,
        "tanggal_pembayaran": lambda p: p.tanggal_bayar,
        "status_pembayaran": lambda p: getattr(transaksi, "status_pembayaran", None),
        "diskon": lambda p: getattr(transaksi, "diskon", None),
        "promo_id": lambda p: getattr(transaksi, "promo_id_promo", None),
        "promo": lambda p: getattr(transaksi, "promo", None),
    })


def alias_point_member(point):
    return _alias_attrs(point, {
        "transaksi_id": lambda p: p.transaksi_id_transaksi,
        "jumlah_poin": lambda p: p.point_masuk,
    })


def alias_transaction(transaksi):
    if transaksi is None:
        return None

    alias = _alias_attrs(transaksi, {
        "tanggal_transaksi": lambda t: t.tanggal,
        "total_harga": lambda t: t.subtotal,
        "total_bayar": lambda t: t.total,
        "status_transaksi": lambda t: MODEL_STATUS_TO_UI.get(t.status_laundry, t.status_laundry),
        "karyawan_id": lambda t: t.users_id_users,
        "promo_id": lambda t: t.promo_id_promo,
        "status_pembayaran": lambda t: getattr(t, "status_pembayaran", None),
        "diskon": lambda t: getattr(t, "diskon", None),
    })

    alias_member(getattr(transaksi, "pelanggan", None))
    alias_payment(getattr(transaksi, "pembayaran", None))

    if hasattr(transaksi, "detail_transaksi"):
        try:
            details = list(transaksi.detail_transaksi)
        except Exception:
            details = None
        if details:
            alias_details(details)

    return alias


def alias_transactions(transactions):
    return [alias_transaction(transaksi) for transaksi in transactions]


def alias_pagination(pagination):
    try:
        pagination.items = [alias_transaction(item) for item in pagination.items]
    except Exception:
        pass
    return pagination
