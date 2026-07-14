import logging
from decimal import Decimal, InvalidOperation
from datetime import datetime
from json import JSONDecodeError
from secrets import token_urlsafe

import requests
from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for, jsonify
from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload

from models import db
from models.layanan import Layanan
from models.member import Pelanggan
from models.transaksi import Transaksi
from models.detail_transaksi import DetailTransaksi
from models.pembayaran import Pembayaran
from models.point_member import PointMember
from models.promo import Promo
from routes.auth import karyawan_required, login_required
from routes.compat import alias_detail, alias_payment, alias_transaction, MODEL_STATUS_TO_UI, UI_STATUS_TO_MODEL
from routes.dashboard import _build_status_summary


kasir_bp = Blueprint("karyawan", __name__, url_prefix="/karyawan")


def _status_class(status):
    # Map model enum values to Bootstrap badge classes
    return {
        "Antrian": "bg-secondary",
        "Diproses": "bg-primary",
        "Siap Diambil": "bg-warning text-dark",
        "Selesai": "bg-success",
    }.get(status, "bg-secondary")


def _display_status(status):
    return "Antrian" if status == "Menunggu" else status


def _model_status(status):
    return UI_STATUS_TO_MODEL.get(status, status)


def _ui_status(status):
    return MODEL_STATUS_TO_UI.get(status, status)


def _best_promo(subtotal):
    promos = Promo.query.filter_by(status="Aktif").all()
    best_promo = None
    best_discount = Decimal("0")

    for promo in promos:
        if subtotal < promo.minimal_transaksi:
            continue

        if promo.tipe_diskon == "Persen":
            discount = subtotal * (promo.nilai_diskon / Decimal("100"))
        else:
            discount = promo.nilai_diskon

        discount = min(discount, subtotal)
        if discount > best_discount:
            best_promo = promo
            best_discount = discount

    return best_promo, best_discount


def _format_currency(value):
    return f"Rp {float(value or 0):,.0f}".replace(",", ".")


def _normalize_whatsapp_number(phone):
    if phone is None:
        return None

    phone = str(phone).strip().replace(" ", "").replace("-", "")
    if not phone:
        return None

    if phone.startswith("+"):
        phone = phone[1:]

    if phone.startswith("0"):
        phone = "62" + phone[1:]
    elif not phone.startswith("62"):
        return None

    return phone if len(phone) >= 10 else None


def _send_whatsapp_notification(transaksi, pelanggan):
    if not transaksi or not pelanggan:
        return False, ""

    api_url = current_app.config.get("WHATSAPP_API_URL", "")
    api_key = current_app.config.get("WHATSAPP_API_KEY", "")
    api_key_status = "loaded" if api_key else "empty"

    if not api_url or not api_key:
        current_app.logger.warning("WhatsApp notification skipped because the API is not configured.")
        return False, ""

    phone = _normalize_whatsapp_number(getattr(pelanggan, "no_hp", None))
    if not phone:
        current_app.logger.warning("WhatsApp notification skipped because the phone number is invalid.")
        return False, ""

    transaction_code = getattr(transaksi, "kode_transaksi", getattr(transaksi, "id_transaksi", "-"))
    current_app.logger.info("WhatsApp API URL: %s", api_url)
    current_app.logger.info("WhatsApp API key status: %s", api_key_status)
    current_app.logger.info("WhatsApp normalized phone: %s", phone)
    current_app.logger.info("WhatsApp transaction code: %s", transaction_code)

    total_value = getattr(transaksi, "total", 0) or 0
    message = (
        f"Halo {getattr(pelanggan, 'nama', '-')}\n\n"
        "Laundry Anda telah selesai diproses dan sudah siap diambil.\n\n"
        "Kode Transaksi:\n"
        f"{getattr(transaksi, 'kode_transaksi', getattr(transaksi, 'id_transaksi', '-'))}\n\n"
        f"Total Pembayaran:\nRp {float(total_value):,.0f}".replace(",", ".") + "\n\n"
        "Silakan datang ke Smart Wash Laundry.\n\n"
        "Terima kasih telah menggunakan Smart Wash Laundry."
    )

    payload = {
        "target": phone,
        "message": message,
    }
    headers = {
        "Authorization": api_key,
    }

    try:
        current_app.logger.info("WhatsApp sending request to Fonnte")
        response = requests.post(api_url, headers=headers, data=payload, timeout=10)
        response_body = response.text
        current_app.logger.info("WhatsApp HTTP Status: %s", response.status_code)
        current_app.logger.info("WhatsApp Response body: %s", response_body)
        response.raise_for_status()

        try:
            response_json = response.json()
        except ValueError:
            current_app.logger.error("WhatsApp response was not valid JSON.")
            return False, ""

        if isinstance(response_json, dict) and response_json.get("status") is False:
            reason = response_json.get("reason") or "Unknown Fonnte error"
            current_app.logger.error("WhatsApp notification failed: %s", reason)
            return False, reason

        return True, ""
    except requests.exceptions.Timeout:
        current_app.logger.exception("WhatsApp notification timed out.")
    except requests.exceptions.ConnectionError:
        current_app.logger.exception("WhatsApp notification connection failed.")
    except requests.exceptions.HTTPError:
        current_app.logger.exception("WhatsApp notification returned an HTTP error.")
    except requests.exceptions.RequestException:
        current_app.logger.exception("WhatsApp notification request failed.")
    except JSONDecodeError:
        current_app.logger.exception("WhatsApp notification response was not valid JSON.")

    return False, ""


def _apply_member_points_for_payment(transaksi, customer, redeem_points=0):
    if not customer or not getattr(customer, "is_member", False):
        return

    final_paid = Decimal(str(transaksi.total or 0))
    points_earned = int(final_paid // Decimal("5000")) if final_paid > 0 else 0

    if redeem_points > 0:
        db.session.add(PointMember(
            pelanggan_id=customer.id,
            transaksi_id_transaksi=transaksi.id_transaksi,
            point_masuk=0,
            point_keluar=redeem_points,
            keterangan="Redeem Point",
        ))

    if points_earned > 0:
        db.session.add(PointMember(
            pelanggan_id=customer.id,
            transaksi_id_transaksi=transaksi.id_transaksi,
            point_masuk=points_earned,
            point_keluar=0,
            keterangan=f"Point Masuk dari transaksi {getattr(transaksi, 'format_id', lambda: transaksi.id_transaksi)()}",
        ))

    customer.total_point = (customer.total_point or 0) - redeem_points + points_earned


def _fetch_qris_payload(transaksi):
    api_url = current_app.config.get("QRIS_API_URL", "") or ""
    api_key = current_app.config.get("QRIS_API_KEY", "") or ""
    amount = float(transaksi.total or 0)
    transaction_code = getattr(transaksi, "kode_transaksi", transaksi.id_transaksi)
    transaction_id = transaksi.id_transaksi

    if not api_url:
        import urllib.parse
        # Generate a dummy QRIS payload (EMVCo format approximation)
        amount_str = str(int(amount))
        qris_data = f"00020101021126670016COM.NOBUBANK.WWW01189360050300000879140214300346369018440315ID102124503463690184520454995303360540{len(amount_str):02d}{amount_str}5802ID5919Smart Wash Laundry6015Jakarta Selatan61051219062160712{transaction_code}6304"
        encoded_data = urllib.parse.quote(qris_data)
        return {
            "note": "Mode Demo: Menampilkan QRIS (Mock API).",
            "amount": amount,
            "transaction_code": transaction_code,
            "qris_url": f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded_data}",
            "provider_response": None,
        }

    payload = {
        "amount": amount,
        "transaction_id": transaction_id,
        "transaction_code": transaction_code,
        "description": f"Pembayaran {transaction_code}",
    }
    headers = {}
    if api_key:
        headers["Authorization"] = api_key

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        response_json = response.json()
        return {
            "note": "QRIS API response berhasil diperoleh.",
            "amount": amount,
            "transaction_code": transaction_code,
            "qris_url": response_json.get("qris_url") if isinstance(response_json, dict) else None,
            "provider_response": response_json,
        }
    except requests.exceptions.RequestException:
        current_app.logger.exception("QRIS API request gagal.")
        return {
            "note": "QRIS API request gagal, gunakan fallback.",
            "amount": amount,
            "transaction_code": transaction_code,
            "qris_url": f"https://example.com/qris-pay/{transaction_id}",
            "provider_response": None,
        }
    except ValueError:
        current_app.logger.exception("QRIS API response tidak valid.")
        return {
            "note": "QRIS API response tidak valid.",
            "amount": amount,
            "transaction_code": transaction_code,
            "qris_url": f"https://example.com/qris-pay/{transaction_id}",
            "provider_response": None,
        }


@kasir_bp.route("/dashboard")
@login_required
@karyawan_required
def dashboard():
    status_summary = _build_status_summary()
    counts = {
        "queue": status_summary.get("Antrian", 0),
        "wash": status_summary.get("Diproses", 0),
        "ready": status_summary.get("Siap Diambil", 0),
    }

    transaksi_list = (
        Transaksi.query
        .filter(Transaksi.status_laundry != "Selesai")
        .order_by(Transaksi.tanggal.desc())
        .limit(3)
        .all()
    )
    transaksi_list = [alias_transaction(transaksi) for transaksi in transaksi_list]
    orders = []
    for transaksi in transaksi_list:
        pelanggan = Pelanggan.query.get(transaksi.pelanggan_id)
        orders.append({
            "id": transaksi.id_transaksi,
            "kode": getattr(transaksi, 'kode_transaksi', transaksi.id_transaksi),
            "pelanggan": pelanggan.nama if pelanggan else "-",
            "layanan": transaksi.catatan or "-",
            "status": transaksi.status_laundry,
            "status_class": _status_class(transaksi.status_laundry),
            "action": "Lihat",
            "action_icon": "bi-eye",
        })
    return render_template("kasir/dashboard.html", orders=orders, counts=counts)


@kasir_bp.route("/transaksi", methods=["GET", "POST"])
@login_required
@karyawan_required
def transaksi():
    if request.method == "POST":
        form_token = request.form.get("form_token", "")
        if not form_token or form_token != session.pop("transaction_form_token", None):
            flash("Transaksi ini sudah diproses atau form tidak valid. Silakan ulangi transaksi.", "warning")
            return redirect(url_for("karyawan.transaksi"))

        pelanggan_id = request.form.get("pelanggan_id", "").strip()
        layanan_id = request.form.get("layanan_id", "").strip()
        berat = request.form.get("berat", "0").strip().replace(",", ".")
        metode_pembayaran = request.form.get("metode_pembayaran", "").strip()
        status_pembayaran = request.form.get("status_pembayaran", "Belum Bayar").strip()
        redeem_points_raw = request.form.get("redeem_points", "").strip()

        try:
            berat_value = Decimal(berat)
        except InvalidOperation:
            flash("Berat harus berupa angka yang valid.", "warning")
            return redirect(url_for("karyawan.transaksi"))

        if not pelanggan_id:
            flash("Pelanggan wajib dipilih.", "warning")
            return redirect(url_for("karyawan.transaksi"))
        if not layanan_id:
            flash("Layanan laundry wajib dipilih.", "warning")
            return redirect(url_for("karyawan.transaksi"))
        if berat_value <= 0:
            flash("Berat harus lebih dari 0 kg.", "warning")
            return redirect(url_for("karyawan.transaksi"))
        if metode_pembayaran not in ("Cash", "QRIS"):
            flash("Metode pembayaran tidak valid.", "warning")
            return redirect(url_for("karyawan.transaksi"))
        if status_pembayaran not in ("Belum Bayar", "Lunas"):
            flash("Status pembayaran tidak valid.", "warning")
            return redirect(url_for("karyawan.transaksi"))

        try:
            customer = Pelanggan.query.get_or_404(int(pelanggan_id))
            layanan_item = Layanan.query.get_or_404(int(layanan_id))
            subtotal = layanan_item.harga_perkg * berat_value
            promo, promo_discount = _best_promo(subtotal)

            redeem_points = 0
            redeem_discount = Decimal("0")
            if customer.is_member and redeem_points_raw:
                try:
                    redeem_points = int(redeem_points_raw)
                except ValueError:
                    redeem_points = 0

                if redeem_points > 0:
                    available_points = int(customer.total_point or 0)
                    if redeem_points < 20:
                        flash("Minimal redeem adalah 20 point.", "warning")
                        return redirect(url_for("karyawan.transaksi"))
                    if redeem_points > available_points:
                        flash("Point yang digunakan melebihi saldo.", "warning")
                        return redirect(url_for("karyawan.transaksi"))
                    if redeem_points % 20 != 0:
                        flash("Point harus kelipatan 20.", "warning")
                        return redirect(url_for("karyawan.transaksi"))

                    redeem_discount = Decimal(redeem_points // 20 * 10000)
                    if redeem_discount > (subtotal - promo_discount):
                        max_points = int(((subtotal - promo_discount) // Decimal("10000")) * 20)
                        flash(f"Point yang ditukar terlalu banyak. Maksimum {max_points} point untuk subtotal ini.", "warning")
                        return redirect(url_for("karyawan.transaksi"))

            # --- Handle Add-Ons ---
            addon_ids = request.form.getlist("addon_ids[]")
            addon_qtys = request.form.getlist("addon_qtys[]")
            addon_total = Decimal("0")
            addon_details = []  # list of (layanan_obj, qty, harga, subtotal)
            for i, aid in enumerate(addon_ids):
                try:
                    addon_layanan = Layanan.query.get(int(aid))
                    if not addon_layanan or addon_layanan.jenis != "AddOn":
                        continue
                    qty = 1
                    if i < len(addon_qtys):
                        try:
                            qty = max(1, int(addon_qtys[i]))
                        except ValueError:
                            qty = 1
                    addon_harga = addon_layanan.harga_perkg
                    addon_sub = addon_harga * qty
                    addon_total += addon_sub
                    addon_details.append((addon_layanan, qty, addon_harga, addon_sub))
                except Exception:
                    continue

            total_subtotal = subtotal + addon_total
            total_discount = promo_discount + redeem_discount
            final_total = max(Decimal("0"), total_subtotal - total_discount)

            # generate kode_transaksi: TRX-YYYYMMDD-XXXX
            today = datetime.now().strftime('%Y%m%d')
            pattern = f"TRX-{today}-%"
            last = Transaksi.query.filter(Transaksi.kode_transaksi.like(pattern)).order_by(Transaksi.kode_transaksi.desc()).first()
            last_num = 0
            if last and getattr(last, 'kode_transaksi', None):
                try:
                    last_num = int(last.kode_transaksi.split('-')[-1])
                except Exception:
                    last_num = 0
            next_num = last_num + 1
            kode_transaksi = f"TRX-{today}-{next_num:04d}"

            transaksi_baru = Transaksi(
                kode_transaksi=kode_transaksi,
                pelanggan_id=customer.id,
                users_id_users=session.get("user_id"),
                status_laundry="Antrian",
                subtotal=total_subtotal,
                diskon=total_discount,
                total=final_total,
                status_pembayaran=status_pembayaran,
                catatan=layanan_item.nama_layanan,
            )
            db.session.add(transaksi_baru)
            db.session.flush()

            # Detail utama
            detail = DetailTransaksi(
                transaksi_id_transaksi=transaksi_baru.id_transaksi,
                layanan_id_layanan=layanan_item.id_layanan,
                berat=berat_value,
                qty=1,
                harga=layanan_item.harga_perkg,
                sub_total=subtotal,
            )
            db.session.add(detail)

            # Detail add-on
            for addon_layanan, qty, addon_harga, addon_sub in addon_details:
                detail_addon = DetailTransaksi(
                    transaksi_id_transaksi=transaksi_baru.id_transaksi,
                    layanan_id_layanan=addon_layanan.id_layanan,
                    berat=None,
                    qty=qty,
                    harga=addon_harga,
                    sub_total=addon_sub,
                )
                db.session.add(detail_addon)

            pembayaran = Pembayaran(
                transaksi_id_transaksi=transaksi_baru.id_transaksi,
                metode=metode_pembayaran,
                tanggal_bayar=datetime.now() if status_pembayaran == "Lunas" else None,
                jumlah_bayar=final_total,
            )
            db.session.add(pembayaran)

            if status_pembayaran == "Lunas":
                _apply_member_points_for_payment(transaksi_baru, customer, redeem_points=redeem_points)

            db.session.commit()

            flash("Transaksi laundry berhasil disimpan.", "success")
            return redirect(url_for("karyawan.transaksi_detail", id_transaksi=transaksi_baru.id_transaksi))
        except Exception as e:
            db.session.rollback()
            flash(f"Transaksi gagal disimpan: {str(e)}", "danger")
            return redirect(url_for("karyawan.transaksi"))

    layanan_utama = Layanan.query.filter_by(jenis="Utama").order_by(Layanan.id_layanan.asc()).all()
    layanan_addon = Layanan.query.filter_by(jenis="AddOn").order_by(Layanan.id_layanan.asc()).all()
    form_token = token_urlsafe(24)
    session["transaction_form_token"] = form_token
    return render_template(
        "kasir/transaksi.html",
        layanan=layanan_utama,
        layanan_addon=layanan_addon,
        form_token=form_token,
    )


@kasir_bp.route("/api/pelanggan")
@login_required
@karyawan_required
def api_pelanggan():
    query_text = request.args.get("q", "").strip()
    query = Pelanggan.query

    if query_text:
        q = f"%{query_text}%"
        query = query.filter(or_(Pelanggan.nama.ilike(q), Pelanggan.no_hp.ilike(q)))

    customers = query.order_by(Pelanggan.nama.asc()).limit(10).all()
    results = []
    for customer in customers:
        transaksi_count = db.session.query(func.count(Transaksi.id_transaksi)).filter(Transaksi.pelanggan_id == customer.id).scalar()
        last_transaction = Transaksi.query.filter_by(
            pelanggan_id=customer.id
        ).order_by(Transaksi.tanggal.desc()).first()
        results.append({
            "id_pelanggan": customer.id,
            "nama": customer.nama,
            "no_hp": customer.no_hp,
            "alamat": customer.alamat or "",
            "is_member": bool(customer.is_member),
            "jenis_pelanggan": customer.jenis_pelanggan,
            "total_point": customer.total_point,
            "total_transaksi": transaksi_count,
            "last_transaction_date": last_transaction.tanggal.strftime("%d/%m/%Y %H:%M") if last_transaction else "-",
        })

    return jsonify(results)


@kasir_bp.route("/api/pelanggan/tambah", methods=["POST"])
@login_required
@karyawan_required
def tambah_pelanggan_api():
    data = request.json or {}
    nama = data.get("nama", "").strip()
    no_hp = data.get("no_hp", "").strip()
    alamat = data.get("alamat", "").strip()

    if not nama or not no_hp or not alamat:
        return jsonify({"error": "Data pelanggan tidak lengkap."}), 400

    if Pelanggan.query.filter_by(no_hp=no_hp).first():
        return jsonify({"error": "Nomor HP sudah digunakan."}), 400

    is_member = data.get("is_member", False)

    customer = Pelanggan(
        nama=nama,
        no_hp=no_hp,
        alamat=alamat,
        is_member=bool(is_member),
        total_point=0,
    )
    db.session.add(customer)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Pelanggan berhasil ditambahkan.",
        "id_pelanggan": customer.id,
        "nama": customer.nama,
        "no_hp": customer.no_hp,
        "alamat": customer.alamat or "",
        "is_member": bool(customer.is_member),
        "jenis_pelanggan": customer.jenis_pelanggan,
        "total_point": customer.total_point,
        "total_transaksi": 0,
        "last_transaction_date": "-",
    })


@kasir_bp.route("/api/transaksi/hitung", methods=["POST"])
@login_required
@karyawan_required
def api_hitung_transaksi():
    data = request.json or {}
    layanan_id = data.get("layanan_id")
    berat = str(data.get("berat", "0")).replace(",", ".")

    try:
        berat_value = Decimal(berat)
    except InvalidOperation:
        return jsonify({"error": "Berat tidak valid."}), 400

    if not layanan_id or berat_value <= 0:
        return jsonify({
            "subtotal": "0",
            "discount": "0",
            "grand_total": "0",
            "promo": None,
            "harga_satuan": "0",
        })

    layanan_item = Layanan.query.get(layanan_id)
    if not layanan_item:
        return jsonify({"error": "Layanan tidak ditemukan."}), 404

    subtotal = layanan_item.harga_perkg * berat_value
    promo, discount = _best_promo(subtotal)
    grand_total = subtotal - discount

    return jsonify({
        "harga_satuan": str(layanan_item.harga_perkg),
        "subtotal": str(subtotal),
        "discount": str(discount),
        "grand_total": str(grand_total),
        "promo": {
            "id": promo.id_promo,
            "nama": promo.nama_promo,
            "nilai": promo.nilai_label(),
        } if promo else None,
    })


@kasir_bp.route("/transaksi/detail/<int:id_transaksi>")
@login_required
@karyawan_required
def transaksi_detail(id_transaksi):
    transaksi_item = Transaksi.query.get_or_404(id_transaksi)
    details = DetailTransaksi.query.filter_by(transaksi_id_transaksi=id_transaksi).all()
    details = [alias_detail(detail) for detail in details]
    pembayaran = alias_payment(Pembayaran.query.filter_by(transaksi_id_transaksi=id_transaksi).first())
    point_history = PointMember.query.filter_by(transaksi_id_transaksi=id_transaksi).all()

    redeem_points = sum(int(item.point_keluar or 0) for item in point_history if (item.keterangan or "").strip() == "Redeem Point")
    redeem_discount = (redeem_points // 20) * 10000
    promo_discount = max(Decimal("0"), (transaksi_item.diskon or Decimal("0")) - Decimal(redeem_discount))
    point_earned = sum(int(item.point_masuk or 0) for item in point_history)
    if point_earned <= 0 and (transaksi_item.total or Decimal("0")) > 0:
        point_earned = int((transaksi_item.total or Decimal("0")) // Decimal("5000"))

    qris_url = None
    if pembayaran and getattr(pembayaran, 'metode_pembayaran', getattr(pembayaran, 'metode', '')) == 'QRIS':
        qris_payload = _fetch_qris_payload(transaksi_item)
        qris_url = qris_payload.get('qris_url') if isinstance(qris_payload, dict) else None

    return render_template(
        "kasir/transaksi_detail.html",
        transaksi=transaksi_item,
        details=details,
        pembayaran=pembayaran,
        promo_discount=promo_discount,
        redeem_discount=Decimal(redeem_discount),
        point_earned=int(point_earned or 0),
        qris_url=qris_url,
        display_status=_display_status,
        format_currency=_format_currency,
    )


@kasir_bp.route("/member")
@login_required
@karyawan_required
def member():
    search = request.args.get("q", "").strip()
    transaksi_counts = db.session.query(
        Transaksi.pelanggan_id.label("pelanggan_id"),
        func.count(Transaksi.id_transaksi).label("total_transaksi")
    ).group_by(Transaksi.pelanggan_id).subquery()

    query = db.session.query(
        Pelanggan,
        func.coalesce(transaksi_counts.c.total_transaksi, 0).label("total_transaksi")
    ).outerjoin(
        transaksi_counts,
        Pelanggan.id == transaksi_counts.c.pelanggan_id
    )

    if search:
        q = f"%{search}%"
        query = query.filter(or_(Pelanggan.nama.ilike(q), Pelanggan.no_hp.ilike(q)))

    rows = query.order_by(Pelanggan.nama.asc()).all()
    member_rows = []
    non_member_rows = []
    for customer, total_transaksi in rows:
        row = {
            "id": customer.id,
            "nama": customer.nama,
            "no_hp": customer.no_hp,
            "alamat": customer.alamat or "-",
            "total_point": customer.total_point,
            "total_transaksi": int(total_transaksi or 0),
        }
        if customer.is_member:
            member_rows.append(row)
        else:
            non_member_rows.append(row)

    return render_template(
        "kasir/member.html",
        member_rows=member_rows,
        non_member_rows=non_member_rows,
        search=search,
    )


@kasir_bp.route("/member/detail/<int:id>")
@login_required
@karyawan_required
def member_detail(id):
    customer = Pelanggan.query.get_or_404(id)
    
    # Get all transactions for this customer
    transactions = Transaksi.query.filter_by(
        pelanggan_id=id
    ).order_by(Transaksi.tanggal.desc()).all()
    
    # Alias transactions for template compatibility
    transactions = [alias_transaction(t) for t in transactions]
    
    # Calculate statistics
    total_transaksi = len(transactions)
    
    # Calculate total spending (sum of all transaction totals)
    total_spending = db.session.query(func.sum(Transaksi.total)).filter_by(
        pelanggan_id=id
    ).scalar() or Decimal("0")
    
    # Get last transaction date
    last_transaksi = db.session.query(Transaksi.tanggal).filter_by(
        pelanggan_id=id
    ).order_by(Transaksi.tanggal.desc()).first()
    last_transaksi_date = last_transaksi[0] if last_transaksi else None
    
    # Get point history
    point_history = PointMember.query.filter_by(
        pelanggan_id=id
    ).order_by(PointMember.tanggal.desc()).all()

    return render_template(
        "kasir/member_detail.html",
        customer=customer,
        transactions=transactions,
        total_transaksi=total_transaksi,
        total_spending=total_spending,
        last_transaksi_date=last_transaksi_date,
        point_history=point_history,
    )


@kasir_bp.route("/member/edit/<int:id>", methods=["GET", "POST"])
@login_required
@karyawan_required
def member_edit(id):
    customer = Pelanggan.query.get_or_404(id)

    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        no_hp = request.form.get("no_hp", "").strip()
        alamat = request.form.get("alamat", "").strip()

        if not nama or not no_hp or not alamat:
            flash("Nama, nomor HP, dan alamat wajib diisi.", "warning")
            return render_template("kasir/member_form.html", customer=customer)

        existing_customer = Pelanggan.query.filter(
            Pelanggan.no_hp == no_hp,
            Pelanggan.id != id
        ).first()
        if existing_customer:
            flash("Nomor HP sudah terdaftar.", "warning")
            return render_template("kasir/member_form.html", customer=customer)

        customer.nama = nama
        customer.no_hp = no_hp
        customer.alamat = alamat
        db.session.commit()

        flash("Data pelanggan berhasil diperbarui.", "success")
        return redirect(url_for("karyawan.member_detail", id=customer.id))

    return render_template("kasir/member_form.html", customer=customer)


@kasir_bp.route("/member/jadikan-member/<int:id>", methods=["POST"])
@login_required
@karyawan_required
def jadikan_member(id):
    customer = Pelanggan.query.get_or_404(id)
    if customer.is_member:
        flash("Pelanggan sudah berstatus Member.", "info")
        return redirect(url_for("karyawan.member"))

    customer.is_member = True
    db.session.commit()
    flash("Pelanggan berhasil dijadikan Member.", "success")
    return redirect(url_for("karyawan.member"))


@kasir_bp.route("/status", methods=["GET", "POST"])
@login_required
@karyawan_required
def status():
    if request.method == "POST":
        transaksi_id = request.form.get("transaksi_id")
        status_value = request.form.get("status")
        valid_statuses = ["Antrian", "Diproses", "Siap Diambil", "Selesai"]
        if status_value not in valid_statuses:
            flash("Status tidak valid.", "warning")
            return redirect(url_for("karyawan.status"))

        transaksi = Transaksi.query.get_or_404(transaksi_id)
        previous_status = transaksi.status_laundry
        transaksi.status_laundry = status_value
        db.session.commit()

        notification_sent = False
        response_body = ""
        if status_value == "Siap Diambil" and previous_status != "Siap Diambil":
            pelanggan = Pelanggan.query.get(transaksi.pelanggan_id)
            try:
                notification_sent, response_body = _send_whatsapp_notification(transaksi, pelanggan)
            except Exception as exc:
                current_app.logger.exception("Unexpected error while sending WhatsApp notification: %s", exc)
                response_body = str(exc)

            if notification_sent:
                flash("Notifikasi WhatsApp berhasil dikirim ke pelanggan.", "success")
            else:
                flash("Status laundry berhasil diperbarui, tetapi notifikasi WhatsApp gagal dikirim.", "warning")
        else:
            flash("Status laundry berhasil diperbarui.", "success")
        return redirect(url_for("karyawan.status"))

    search = request.values.get("q", "").strip()
    status_filter = request.values.get("status", "").strip()
    orders = Transaksi.query.order_by(Transaksi.tanggal.desc())

    if not status_filter:
        orders = orders.filter(Transaksi.status_laundry != "Selesai")

    if search:
        q = f"%{search}%"
        orders = orders.join(Pelanggan, Transaksi.pelanggan_id == Pelanggan.id).filter(
            or_(Pelanggan.nama.ilike(q), Pelanggan.no_hp.ilike(q), Transaksi.id_transaksi.like(q))
        )

    if status_filter in ["Antrian", "Diproses", "Siap Diambil", "Selesai"]:
        orders = orders.filter(Transaksi.status_laundry == _model_status(status_filter))
    orders = orders.all()
    result = []
    for transaksi in orders:
        pelanggan = Pelanggan.query.get(transaksi.pelanggan_id)
        result.append({
            "id": transaksi.id_transaksi,
            "kode": getattr(transaksi, "kode_transaksi", transaksi.id_transaksi),
            "tanggal": transaksi.tanggal.strftime("%d/%m/%Y %H:%M"),
            "pelanggan": pelanggan.nama if pelanggan else "-",
            "whatsapp": pelanggan.no_hp if pelanggan else "-",
            "status": _ui_status(transaksi.status_laundry),
            "status_class": _status_class(_ui_status(transaksi.status_laundry)),
        })

    return render_template("kasir/status.html", orders=result, search=search, status_filter=status_filter)


@kasir_bp.route("/pembayaran", methods=["GET", "POST"])
@login_required
@karyawan_required
def pembayaran():
    if request.method == "POST":
        transaksi_id = request.form.get("transaksi_id")
        metode = request.form.get("metode", "").strip()

        if not transaksi_id:
            flash("Transaksi tidak ditemukan.", "warning")
            return redirect(url_for("karyawan.pembayaran"))

        if metode not in ("Cash", "QRIS"):
            flash("Metode pembayaran tidak valid.", "warning")
            return redirect(url_for("karyawan.pembayaran"))

        try:
            transaksi = Transaksi.query.get_or_404(int(transaksi_id))
            if transaksi.status_pembayaran != "Belum Bayar":
                flash("Transaksi tidak tersedia untuk pembayaran.", "warning")
                return redirect(url_for("karyawan.pembayaran"))

            pelanggan = Pelanggan.query.get(transaksi.pelanggan_id)

            jumlah = transaksi.total or 0
            pembayaran = Pembayaran(
                transaksi_id_transaksi=transaksi.id_transaksi,
                metode=metode,
                jumlah_bayar=jumlah,
                tanggal_bayar=datetime.now(),
            )
            db.session.add(pembayaran)

            transaksi.status_pembayaran = "Lunas"
            if transaksi.status_laundry == "Siap Diambil":
                transaksi.status_laundry = "Selesai"

            if pelanggan and getattr(pelanggan, 'is_member', False):
                _apply_member_points_for_payment(transaksi, pelanggan, redeem_points=0)

            db.session.commit()
            flash("Pembayaran berhasil.", "success")
            return redirect(url_for("karyawan.pembayaran"))
        except Exception as e:
            db.session.rollback()
            flash(f"Pembayaran gagal: {str(e)}", "danger")
            return redirect(url_for("karyawan.pembayaran"))

    # GET
    search = request.args.get("q", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    query = Transaksi.query.join(Pelanggan, Transaksi.pelanggan_id == Pelanggan.id).filter(
        Transaksi.status_pembayaran == "Belum Bayar",
    )

    if search:
        q = f"%{search}%"
        query = query.filter(or_(Pelanggan.nama.ilike(q), Pelanggan.no_hp.ilike(q), Transaksi.kode_transaksi.ilike(q)))

    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Transaksi.tanggal >= start)
        except ValueError:
            pass

    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(Transaksi.tanggal <= end)
        except ValueError:
            pass

    orders = query.order_by(Transaksi.tanggal.desc()).all()
    result = []
    for transaksi in orders:
        pelanggan = Pelanggan.query.get(transaksi.pelanggan_id)
        subtotal = getattr(transaksi, 'subtotal', 0) or 0
        total = getattr(transaksi, 'total', 0) or 0
        discount = subtotal - total if subtotal and total else Decimal("0")

        result.append({
            "id": transaksi.id_transaksi,
            "kode": getattr(transaksi, 'kode_transaksi', transaksi.id_transaksi),
            "pelanggan": pelanggan.nama if pelanggan else "-",
            "no_hp": pelanggan.no_hp if pelanggan else "-",
            "tanggal": transaksi.tanggal.strftime("%d/%m/%Y") if transaksi.tanggal else "-",
            "subtotal": subtotal,
            "discount": discount,
            "total": total,
        })

    return render_template(
        "kasir/pembayaran.html",
        orders=result,
        search=search,
        start_date=start_date,
        end_date=end_date,
        format_currency=_format_currency,
    )


@kasir_bp.route("/qris", methods=["GET"])
@login_required
@karyawan_required
def qris():
    transaksi_id = request.args.get("transaksi_id")
    if not transaksi_id:
        return jsonify(success=False, message="Transaksi tidak ditemukan."), 400

    try:
        transaksi = Transaksi.query.get_or_404(int(transaksi_id))
        if transaksi.status_pembayaran != "Belum Bayar":
            return jsonify(success=False, message="Transaksi tidak tersedia untuk QRIS."), 400

        qris_payload = _fetch_qris_payload(transaksi)
        return jsonify(success=True, qris=qris_payload)
    except Exception as e:
        current_app.logger.exception("Gagal menyiapkan data QRIS.")
        return jsonify(success=False, message=str(e)), 500


@kasir_bp.route("/api/qris/generate", methods=["POST"])
@login_required
@karyawan_required
def api_qris_generate():
    data = request.json or {}
    amount = float(data.get("amount", 0))
    # Dummy transaction code just for display purposes
    transaction_code = "TRX-PREVIEW"
    
    import urllib.parse
    amount_str = str(int(amount))
    qris_data = f"00020101021126670016COM.NOBUBANK.WWW01189360050300000879140214300346369018440315ID102124503463690184520454995303360540{len(amount_str):02d}{amount_str}5802ID5919Smart Wash Laundry6015Jakarta Selatan61051219062160712{transaction_code}6304"
    encoded_data = urllib.parse.quote(qris_data)
    
    qris_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded_data}"
    return jsonify(success=True, qris_url=qris_url)


@kasir_bp.route('/riwayat')
@login_required
@karyawan_required
def riwayat():
    search = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()
    payment_status = request.args.get('payment_status', '').strip()

    query = Transaksi.query.options(selectinload(Transaksi.pelanggan)).join(Pelanggan, Transaksi.pelanggan_id == Pelanggan.id)

    if search:
        q = f"%{search}%"
        query = query.filter(or_(Transaksi.kode_transaksi.ilike(q), Pelanggan.nama.ilike(q), Pelanggan.no_hp.ilike(q)))

    if status_filter in ["Antrian", "Diproses", "Siap Diambil", "Selesai"]:
        query = query.filter(Transaksi.status_laundry == status_filter)

    if payment_status in ["Belum Bayar", "Lunas"]:
        query = query.filter(Transaksi.status_pembayaran == payment_status)

    orders = query.order_by(Transaksi.tanggal.desc()).all()
    result = []
    for transaksi in orders:
        pelanggan = transaksi.pelanggan
        result.append({
            'id': transaksi.id_transaksi,
            'kode': getattr(transaksi, 'kode_transaksi', transaksi.id_transaksi),
            'tanggal': transaksi.tanggal.strftime('%d/%m/%Y %H:%M') if transaksi.tanggal else '-',
            'pelanggan': pelanggan.nama if pelanggan else '-',
            'no_hp': pelanggan.no_hp if pelanggan else '-',
            'total': transaksi.total,
            'status_laundry': transaksi.status_laundry,
            'status_pembayaran': transaksi.status_pembayaran,
            'status_laundry_class': _status_class(transaksi.status_laundry),
            'status_pembayaran_class': 'bg-success' if transaksi.status_pembayaran == 'Lunas' else 'bg-danger',
        })

    return render_template('kasir/riwayat.html', orders=result, search=search, status_filter=status_filter, payment_status=payment_status, format_currency=_format_currency)


@kasir_bp.route('/riwayat/detail/<int:id_transaksi>')
@login_required
@karyawan_required
def riwayat_detail(id_transaksi):
    transaksi = Transaksi.query.get_or_404(id_transaksi)
    pelanggan = Pelanggan.query.get(transaksi.pelanggan_id)
    details = DetailTransaksi.query.options(selectinload(DetailTransaksi.layanan)).filter_by(transaksi_id_transaksi=id_transaksi).all()
    layanan_list = []
    for d in details:
        layanan_item = d.layanan
        layanan_list.append({
            'nama': layanan_item.nama_layanan if layanan_item else '-',
            'berat': float(d.berat if d.berat is not None else 0),
            'qty': d.qty if getattr(d, 'qty', None) is not None else 1,
            'jenis': getattr(layanan_item, 'jenis', 'Utama') if layanan_item else 'Utama',
            'satuan': getattr(layanan_item, 'satuan', 'perkg') if layanan_item else 'perkg',
            'harga': float(d.harga if d.harga is not None else 0),
            'sub_total': float(d.sub_total if d.sub_total is not None else 0),
        })

    pembayaran = Pembayaran.query.filter_by(transaksi_id_transaksi=id_transaksi).first()

    subtotal = float(transaksi.subtotal or 0)
    total = float(transaksi.total or 0)
    discount = subtotal - total if subtotal and total else 0
    qris_url = None
    if pembayaran and pembayaran.metode == 'QRIS' and transaksi.status_pembayaran == 'Belum Bayar':
        try:
            qris_payload = _fetch_qris_payload(transaksi)
            qris_url = qris_payload.get('qris_url') if isinstance(qris_payload, dict) else None
        except Exception as e:
            current_app.logger.error(f"Failed to fetch QRIS payload in riwayat_detail: {e}")

    return jsonify({
        'id': transaksi.id_transaksi,
        'kode': getattr(transaksi, 'kode_transaksi', transaksi.id_transaksi),
        'tanggal': transaksi.tanggal.strftime('%d/%m/%Y %H:%M') if transaksi.tanggal else '-',
        'pelanggan': {
            'nama': pelanggan.nama if pelanggan else '-',
            'no_hp': pelanggan.no_hp if pelanggan else '-',
            'alamat': pelanggan.alamat if pelanggan else '-',
            'is_member': bool(pelanggan.is_member) if pelanggan else False,
        },
        'layanan': layanan_list,
        'subtotal': subtotal,
        'discount': discount,
        'total': total,
        'status_laundry': transaksi.status_laundry,
        'status_pembayaran': transaksi.status_pembayaran,
        'metode_pembayaran': pembayaran.metode if pembayaran else None,
        'qris_url': qris_url,
    })
