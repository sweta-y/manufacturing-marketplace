import os
from flask import Blueprint, request, redirect, url_for, session, flash
from app.extensions import db
from app.utils.auth_decorators import role_required
from app.services.file_service import create_signed_url, save_upload
from app.services.matching_service import (
    find_matching_manufacturers,
    find_matching_manufacturers_via_hash,
)
from app.services.cost_service import estimate_cost
from app.pyui.customer_pages import (
    dashboard_page,
    upload_step1_page,
    upload_configure_page,
    upload_matches_page,
    upload_confirm_page,
    saved_designs_page,
    orders_page,
    order_detail_page,
    profile_page,
)

customer_bp = Blueprint("customer", __name__, url_prefix="/customer")

UPLOAD_BASE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads"
)


def get_customer_profile_id():
    row = db.session.execute(
        db.text("SELECT customer_profile_id FROM customer_profiles WHERE user_id = :uid"),
        {"uid": session["user_id"]},
    ).first()
    return row[0] if row else None


def _load_lookups():
    processes = db.session.execute(
        db.text("SELECT process_id, name FROM manufacturing_processes")
    ).mappings().all()
    materials = db.session.execute(
        db.text("SELECT material_id, name, process_id FROM materials")
    ).mappings().all()
    return [dict(p) for p in processes], [dict(m) for m in materials]


def _materials_for_process(materials, process_id):
    if not process_id:
        return materials
    return [m for m in materials if str(m["process_id"]) == str(process_id)]


def _owned_request(request_id, cp_id):
    return db.session.execute(
        db.text(
            """SELECT r.*, uf.filename, uf.file_type
               FROM manufacturing_requests r
               LEFT JOIN uploaded_files uf ON uf.file_id = r.file_id
               WHERE r.request_id = :rid AND r.customer_profile_id = :cp"""
        ),
        {"rid": request_id, "cp": cp_id},
    ).mappings().first()


@customer_bp.route("/dashboard")
@role_required("customer")
def dashboard():
    cp_id = get_customer_profile_id()
    order_count = 0
    draft_design_count = 0
    if cp_id:
        row = db.session.execute(
            db.text(
                """SELECT COUNT(*) FROM orders o
                   JOIN manufacturing_requests r ON r.request_id = o.request_id
                   WHERE r.customer_profile_id = :cp"""
            ),
            {"cp": cp_id},
        ).first()
        order_count = row[0] if row else 0

        draft_row = db.session.execute(
            db.text(
                """SELECT COUNT(*)
                   FROM manufacturing_requests r
                   JOIN uploaded_files uf ON uf.file_id = r.file_id
                   WHERE r.customer_profile_id = :cp
                     AND r.status = 'draft'
                     AND NOT EXISTS (
                         SELECT 1 FROM orders o WHERE o.request_id = r.request_id
                     )"""
            ),
            {"cp": cp_id},
        ).first()
        draft_design_count = draft_row[0] if draft_row else 0

    return dashboard_page(
        order_count=order_count,
        draft_design_count=draft_design_count,
    )


@customer_bp.route("/upload", methods=["GET", "POST"])
@role_required("customer")
def upload_design():
    if request.method == "GET":
        return upload_step1_page(step=1)

    cp_id = get_customer_profile_id()
    if not cp_id:
        flash("Customer profile not found.", "error")
        return redirect(url_for("customer.upload_design"))

    if "file" not in request.files or not request.files["file"].filename:
        flash("Please choose a file to upload.", "error")
        return redirect(url_for("customer.upload_design"))

    f = request.files["file"]
    try:
        info = save_upload(f, session["user_id"], UPLOAD_BASE)
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("customer.upload_design"))

    file_row = db.session.execute(
        db.text(
            """INSERT INTO uploaded_files (user_id, filename, file_type, file_size_kb, storage_path)
               VALUES (:uid, :fn, :ft, :fs, :sp) RETURNING file_id"""
        ),
        {
            "uid": session["user_id"],
            "fn": info["filename"],
            "ft": info["file_type"],
            "fs": info["file_size_kb"],
            "sp": info["storage_path"],
        },
    ).first()
    file_id = file_row[0]

    req_row = db.session.execute(
        db.text(
            """INSERT INTO manufacturing_requests (customer_profile_id, file_id, status)
               VALUES (:cp, :fid, 'draft') RETURNING request_id"""
        ),
        {"cp": cp_id, "fid": file_id},
    ).first()
    db.session.commit()

    flash(f"Uploaded {info['filename']} ({info['file_size_kb']} KB).", "success")
    return redirect(url_for("customer.upload_configure", request_id=req_row[0]))


@customer_bp.route("/upload/<int:request_id>/configure", methods=["GET", "POST"])
@role_required("customer")
def upload_configure(request_id):
    cp_id = get_customer_profile_id()
    req = _owned_request(request_id, cp_id)
    if not req:
        flash("Request not found.", "error")
        return redirect(url_for("customer.upload_design"))

    processes, materials = _load_lookups()

    if request.method == "GET":
        selected_process = request.args.get("process_id") or (processes[0]["process_id"] if processes else None)
        filtered_materials = _materials_for_process(materials, selected_process)
        selected_material = filtered_materials[0]["material_id"] if filtered_materials else ""
        quantity = req.get("quantity") or 1
        
        # Get cost estimate if process and material are selected
        cost_estimate = None
        if selected_process and selected_material:
            try:
                cost_estimate = estimate_cost(selected_process, selected_material, quantity)
            except Exception:
                cost_estimate = {"error": "Could not calculate cost", "fallback": True}
        
        return upload_configure_page(
            req=req,
            processes=processes,
            materials=filtered_materials,
            all_materials=materials,
            selected_process=selected_process,
            cost_estimate=cost_estimate,
            form={
                "process_id": selected_process,
                "material_id": selected_material,
                "quantity": quantity,
                "surface_finish": req.get("surface_finish") or "Standard",
                "notes": req.get("notes") or "",
            },
            step=2,
        )

    process_id = request.form.get("process_id")
    material_id = request.form.get("material_id")
    quantity = request.form.get("quantity")
    surface_finish = request.form.get("surface_finish", "Standard")
    notes = request.form.get("notes", "")

    if request.form.get("action") == "refresh_materials":
        return redirect(
            url_for("customer.upload_configure", request_id=request_id, process_id=process_id)
        )

    if request.form.get("action") == "recalculate_estimate":
        return redirect(
            url_for("customer.upload_configure", request_id=request_id, process_id=process_id)
        )

    db.session.execute(
        db.text(
            """UPDATE manufacturing_requests SET
               process_id=:pid, material_id=:mid, quantity=:qty,
               surface_finish=:sf, notes=:notes, status='submitted'
               WHERE request_id=:rid"""
        ),
        {
            "pid": process_id,
            "mid": material_id,
            "qty": quantity,
            "sf": surface_finish,
            "notes": notes,
            "rid": request_id,
        },
    )
    db.session.commit()

    return redirect(url_for("customer.upload_matches", request_id=request_id))


@customer_bp.route("/upload/<int:request_id>/matches", methods=["GET", "POST"])
@role_required("customer")
def upload_matches(request_id):
    cp_id = get_customer_profile_id()
    row = db.session.execute(
        db.text(
            """SELECT process_id, material_id, quantity FROM manufacturing_requests
               WHERE request_id=:rid AND customer_profile_id=:cp"""
        ),
        {"rid": request_id, "cp": cp_id},
    ).mappings().first()
    if not row:
        flash("Request not found.", "error")
        return redirect(url_for("customer.upload_design"))

    matches, used_fallback = find_matching_manufacturers_via_hash(
        row["process_id"], row["material_id"], row["quantity"]
    )

    if request.method == "GET":
        return upload_matches_page(
            request_id=request_id,
            matches=matches,
            step=3,
        )

    manufacturer_profile_id = request.form.get("manufacturer_profile_id")
    machine_id = request.form.get("machine_id")
    if not manufacturer_profile_id or not machine_id:
        flash("Please select a manufacturer.", "error")
        return redirect(url_for("customer.upload_matches", request_id=request_id))

    owner = db.session.execute(
        db.text(
            "SELECT request_id FROM manufacturing_requests WHERE request_id=:rid AND customer_profile_id=:cp"
        ),
        {"rid": request_id, "cp": cp_id},
    ).first()
    if not owner:
        flash("Request not found.", "error")
        return redirect(url_for("customer.upload_design"))

    order_row = db.session.execute(
        db.text(
            """INSERT INTO orders (request_id, manufacturer_profile_id, machine_id, status)
               VALUES (:rid, :mpid, :mid, 'Request Submitted') RETURNING order_id"""
        ),
        {"rid": request_id, "mpid": manufacturer_profile_id, "mid": machine_id},
    ).first()
    order_id = order_row[0]

    db.session.execute(
        db.text(
            """INSERT INTO order_status_history (order_id, status, changed_by, remarks)
               VALUES (:oid, 'Request Submitted', :uid, 'Order created by customer')"""
        ),
        {"oid": order_id, "uid": session["user_id"]},
    )
    db.session.execute(
        db.text("UPDATE manufacturing_requests SET status='matched' WHERE request_id=:rid"),
        {"rid": request_id},
    )
    db.session.commit()

    return redirect(url_for("customer.upload_confirm", request_id=request_id, order_id=order_id))


@customer_bp.route("/upload/<int:request_id>/confirm")
@role_required("customer")
def upload_confirm(request_id):
    cp_id = get_customer_profile_id()
    order_id = request.args.get("order_id", type=int)
    if not order_id:
        flash("Order not found.", "error")
        return redirect(url_for("customer.orders"))

    order = db.session.execute(
        db.text(
            """SELECT o.order_id, mp.business_name
               FROM orders o
               JOIN manufacturing_requests r ON r.request_id = o.request_id
               JOIN manufacturer_profiles mp ON mp.manufacturer_profile_id = o.manufacturer_profile_id
               WHERE o.order_id=:oid AND r.request_id=:rid AND r.customer_profile_id=:cp"""
        ),
        {"oid": order_id, "rid": request_id, "cp": cp_id},
    ).mappings().first()
    if not order:
        flash("Order not found.", "error")
        return redirect(url_for("customer.orders"))

    return upload_confirm_page(
        order=order,
        step=4,
    )


@customer_bp.route("/saved-designs")
@role_required("customer")
def saved_designs():
    rows = db.session.execute(
        db.text(
            """SELECT uf.file_id, uf.filename, uf.uploaded_at,
                        r.request_id, r.status AS request_status,
                        o.order_id
               FROM uploaded_files uf
               LEFT JOIN manufacturing_requests r ON r.file_id = uf.file_id
               LEFT JOIN orders o ON o.request_id = r.request_id
               WHERE uf.user_id = :uid
               ORDER BY uf.uploaded_at DESC"""
        ),
        {"uid": session["user_id"]},
    ).mappings().all()

    designs = []
    for row in rows:
        request_id = row["request_id"]
        order_id = row["order_id"]
        if order_id:
            status = f"Used in Order #{order_id}"
            action_label = "View Order"
            action_url = url_for("customer.order_detail", order_id=order_id)
        else:
            request_status = (row["request_status"] or "draft").lower()
            if request_status == "draft":
                status = "Draft — not yet ordered"
            elif request_status == "submitted":
                status = "Submitted — not yet ordered"
            else:
                status = "Saved design — not yet ordered"
            action_label = "Continue"
            action_url = url_for("customer.upload_configure", request_id=request_id) if request_id else None

        designs.append(
            {
                "file_id": row["file_id"],
                "filename": row["filename"],
                "uploaded_at": row["uploaded_at"],
                "status": status,
                "action_label": action_label,
                "action_url": action_url,
                "download_url": url_for("customer.download_file", file_id=row["file_id"]),
            }
        )

    return saved_designs_page(
        designs=designs,
    )


@customer_bp.route("/files/<int:file_id>")
@role_required("customer")
def download_file(file_id):
    row = db.session.execute(
        db.text(
            "SELECT filename, storage_path FROM uploaded_files "
            "WHERE file_id=:fid AND user_id=:uid"
        ),
        {"fid": file_id, "uid": session["user_id"]},
    ).mappings().first()
    if not row:
        flash("File not found.", "error")
        return redirect(url_for("customer.saved_designs"))
    signed_url = create_signed_url(row["storage_path"])
    if not signed_url:
        flash("Could not create a secure file link.", "error")
        return redirect(url_for("customer.saved_designs"))
    return redirect(signed_url)


@customer_bp.route("/orders")
@role_required("customer")
def orders():
    cp_id = get_customer_profile_id()
    rows = db.session.execute(
        db.text(
            """SELECT o.order_id, o.status, o.created_at, o.final_cost,
               mp.business_name, r.quantity, p.name AS process_name, mt.name AS material_name
               FROM orders o
               JOIN manufacturing_requests r ON r.request_id = o.request_id
               JOIN manufacturer_profiles mp ON mp.manufacturer_profile_id = o.manufacturer_profile_id
               LEFT JOIN manufacturing_processes p ON p.process_id = r.process_id
               LEFT JOIN materials mt ON mt.material_id = r.material_id
               WHERE r.customer_profile_id = :cp
               ORDER BY o.created_at DESC"""
        ),
        {"cp": cp_id},
    ).mappings().all()

    return orders_page(
        orders=[dict(r) for r in rows],
    )


@customer_bp.route("/orders/<int:order_id>")
@role_required("customer")
def order_detail(order_id):
    cp_id = get_customer_profile_id()
    order = db.session.execute(
        db.text(
            """SELECT o.*, mp.business_name, r.quantity, r.surface_finish, r.notes,
               p.name AS process_name, mt.name AS material_name
               FROM orders o
               JOIN manufacturing_requests r ON r.request_id = o.request_id
               JOIN manufacturer_profiles mp ON mp.manufacturer_profile_id = o.manufacturer_profile_id
               LEFT JOIN manufacturing_processes p ON p.process_id = r.process_id
               LEFT JOIN materials mt ON mt.material_id = r.material_id
               WHERE o.order_id=:oid AND r.customer_profile_id=:cp"""
        ),
        {"oid": order_id, "cp": cp_id},
    ).mappings().first()
    if not order:
        flash("Order not found.", "error")
        return redirect(url_for("customer.orders"))

    history = db.session.execute(
        db.text(
            """SELECT status, changed_at, remarks FROM order_status_history
               WHERE order_id=:oid ORDER BY changed_at ASC"""
        ),
        {"oid": order_id},
    ).mappings().all()

    return order_detail_page(
        order=dict(order),
        history=[dict(h) for h in history],
    )


@customer_bp.route("/profile", methods=["GET", "POST"])
@role_required("customer")
def profile():
    if request.method == "GET":
        row = db.session.execute(
            db.text(
                """SELECT u.full_name, u.email, u.phone, cp.company_name, cp.address
                   FROM users u JOIN customer_profiles cp ON cp.user_id = u.user_id
                   WHERE u.user_id = :uid"""
            ),
            {"uid": session["user_id"]},
        ).mappings().first()
        profile_data = dict(row) if row else {}
        return profile_page(
            profile=profile_data,
        )

    db.session.execute(
        db.text("UPDATE customer_profiles SET company_name=:cn, address=:addr WHERE user_id=:uid"),
        {
            "cn": request.form.get("company_name"),
            "addr": request.form.get("address"),
            "uid": session["user_id"],
        },
    )
    db.session.execute(
        db.text(
            "UPDATE users SET full_name=COALESCE(:fn, full_name), phone=COALESCE(:ph, phone) WHERE user_id=:uid"
        ),
        {
            "fn": request.form.get("full_name"),
            "ph": request.form.get("phone"),
            "uid": session["user_id"],
        },
    )
    db.session.commit()
    flash("Profile updated successfully.", "success")
    return redirect(url_for("customer.profile"))
