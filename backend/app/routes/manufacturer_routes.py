from flask import Blueprint, request, redirect, url_for, session, flash
from app.extensions import db
from app.services.notification_service import notify_order_customer, notify_user
from app.utils.auth_decorators import role_required
from app.pyui.manufacturer_pages import (
    status_page as status_page_html,
    dashboard_page,
    profile_page,
    machines_page,
    machine_form_page,
    available_requests_page,
    reject_order_page,
    active_orders_page,
    advance_order_page,
    completed_orders_page,
)
from app.services.priority_service import order_requests_by_priority
from app.services.pricing_service import manufacturer_price_limit, parse_price, valid_manufacturer_quote
from app.pyui.helpers import format_cost

manufacturer_bp = Blueprint("manufacturer", __name__, url_prefix="/manufacturer")

ACTIVE_STATUSES = ("Accepted", "Manufacturing", "Quality Check")
NEXT_STATUS = {
    "Accepted": "Manufacturing",
    "Manufacturing": "Quality Check",
    "Quality Check": "Completed",
}


def _require_approved_manufacturer(f):
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login", next=request.url))
        if session.get("role") != "manufacturer":
            flash("You do not have permission to access that page.", "error")
            return redirect(url_for("auth.login"))

        profile = db.session.execute(
            db.text(
                "SELECT approval_status, rejection_reason FROM manufacturer_profiles WHERE user_id = :uid"
            ),
            {"uid": session["user_id"]},
        ).mappings().first()

        if profile and profile["approval_status"] in ("pending", "rejected"):
            return redirect(url_for("manufacturer.status_page"))

        return f(*args, **kwargs)

    return wrapper


def get_manufacturer_profile_id():
    row = db.session.execute(
        db.text("SELECT manufacturer_profile_id FROM manufacturer_profiles WHERE user_id = :uid"),
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


def _list_machines(mp_id):
    rows = db.session.execute(
        db.text(
            """SELECT m.machine_id, m.machine_name, m.process_id, m.max_dimensions, m.is_active,
               p.name AS process_name
               FROM machines m
               LEFT JOIN manufacturing_processes p ON p.process_id = m.process_id
               WHERE m.manufacturer_profile_id = :mp
               ORDER BY m.created_at DESC"""
        ),
        {"mp": mp_id},
    ).mappings().all()
    machines = []
    for m in rows:
        caps = db.session.execute(
            db.text(
                """SELECT c.capability_id, c.material_id, c.max_quantity, mt.name AS material_name
                   FROM machine_capabilities c
                   LEFT JOIN materials mt ON mt.material_id = c.material_id
                   WHERE c.machine_id = :mid"""
            ),
            {"mid": m["machine_id"]},
        ).mappings().all()
        md = dict(m)
        md["capabilities"] = [dict(c) for c in caps]
        machines.append(md)
    return machines


def _get_owned_order(order_id, mp_id):
    return db.session.execute(
        db.text(
            """SELECT o.order_id, o.status, r.estimated_cost AS customer_price,
                      r.process_id, r.material_id, r.quantity
               FROM orders o
               JOIN manufacturing_requests r ON r.request_id = o.request_id
               WHERE o.order_id=:oid AND o.manufacturer_profile_id=:mp"""
        ),
        {"oid": order_id, "mp": mp_id},
    ).mappings().first()


def _owned_machine(machine_id, mp_id):
    return db.session.execute(
        db.text("SELECT * FROM machines WHERE machine_id=:mid AND manufacturer_profile_id=:mp"),
        {"mid": machine_id, "mp": mp_id},
    ).mappings().first()


@manufacturer_bp.route("/status")
@role_required("manufacturer")
def status_page():
    profile = db.session.execute(
        db.text(
            "SELECT approval_status, rejection_reason FROM manufacturer_profiles WHERE user_id = :uid"
        ),
        {"uid": session["user_id"]},
    ).mappings().first()
    approval_status = profile["approval_status"] if profile else "pending"
    reason = profile["rejection_reason"] if profile else None

    if approval_status == "approved":
        return redirect(url_for("manufacturer.dashboard"))

    if approval_status == "rejected":
        message = "Your registration was rejected."
        if reason:
            message = f"{message} Reason: {reason}"
    else:
        message = "Your account is pending approval."

    return status_page_html(
        message=message,
        approval_status=approval_status,
        rejection_reason=reason,
    )


@manufacturer_bp.route("/dashboard")
@role_required("manufacturer")
@_require_approved_manufacturer
def dashboard():
    mp_id = get_manufacturer_profile_id()
    stats = {"machines": 0, "available": 0, "active": 0}
    if mp_id:
        stats["machines"] = db.session.execute(
            db.text("SELECT COUNT(*) FROM machines WHERE manufacturer_profile_id=:mp AND is_active=TRUE"),
            {"mp": mp_id},
        ).scalar() or 0
        stats["available"] = db.session.execute(
            db.text(
                "SELECT COUNT(*) FROM orders WHERE manufacturer_profile_id=:mp AND status='Request Submitted'"
            ),
            {"mp": mp_id},
        ).scalar() or 0
        stats["active"] = db.session.execute(
            db.text(
                """SELECT COUNT(*) FROM orders
                   WHERE manufacturer_profile_id=:mp AND status IN ('Accepted', 'Manufacturing', 'Quality Check')"""
            ),
            {"mp": mp_id},
        ).scalar() or 0

    return dashboard_page(
        stats=stats,
    )


@manufacturer_bp.route("/profile", methods=["GET", "POST"])
@role_required("manufacturer")
@_require_approved_manufacturer
def profile():
    if request.method == "GET":
        row = db.session.execute(
            db.text(
                """SELECT u.full_name, u.email, u.phone, mp.business_name, mp.address, mp.approval_status
                   FROM users u JOIN manufacturer_profiles mp ON mp.user_id = u.user_id
                   WHERE u.user_id = :uid"""
            ),
            {"uid": session["user_id"]},
        ).mappings().first()
        return profile_page(
            profile=dict(row) if row else {},
        )

    db.session.execute(
        db.text(
            "UPDATE manufacturer_profiles SET business_name=COALESCE(:bn, business_name), address=:addr WHERE user_id=:uid"
        ),
        {
            "bn": request.form.get("business_name"),
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
    return redirect(url_for("manufacturer.profile"))


@manufacturer_bp.route("/machines")
@role_required("manufacturer")
@_require_approved_manufacturer
def machines():
    mp_id = get_manufacturer_profile_id()
    return machines_page(
        machines=_list_machines(mp_id),
    )


@manufacturer_bp.route("/machines/new", methods=["GET", "POST"])
@role_required("manufacturer")
@_require_approved_manufacturer
def machine_new():
    processes, materials = _load_lookups()

    if request.method == "GET":
        selected_process = request.args.get("process_id") or (processes[0]["process_id"] if processes else None)
        return machine_form_page(
            page_title="Add Machine",
            machine=None,
            processes=processes,
            materials=_materials_for_process(materials, selected_process),
            existing_capabilities=[],
            form={
                "machine_name": "",
                "process_id": selected_process,
                "max_dimensions": "",
            },
        )

    mp_id = get_manufacturer_profile_id()
    machine_name = request.form.get("machine_name", "").strip()
    if not machine_name:
        flash("Machine name is required.", "error")
        return redirect(url_for("manufacturer.machine_new"))

    process_id = request.form.get("process_id") or None
    max_dimensions = request.form.get("max_dimensions") or None

    row = db.session.execute(
        db.text(
            """INSERT INTO machines (manufacturer_profile_id, machine_name, process_id, max_dimensions, is_active)
               VALUES (:mp, :name, :pid, :dims, TRUE) RETURNING machine_id"""
        ),
        {"mp": mp_id, "name": machine_name, "pid": process_id, "dims": max_dimensions},
    ).first()
    machine_id = row[0]

    material_ids = request.form.getlist("cap_material_id")
    quantities = request.form.getlist("cap_max_quantity")
    for mat_id, qty in zip(material_ids, quantities):
        if mat_id:
            db.session.execute(
                db.text(
                    """INSERT INTO machine_capabilities (machine_id, material_id, max_quantity)
                       VALUES (:mid, :matid, :mq)"""
                ),
                {"mid": machine_id, "matid": mat_id, "mq": qty or 1000},
            )

    db.session.commit()
    flash("Machine created.", "success")
    return redirect(url_for("manufacturer.machines"))


@manufacturer_bp.route("/machines/<int:machine_id>/edit", methods=["GET", "POST"])
@role_required("manufacturer")
@_require_approved_manufacturer
def machine_edit(machine_id):
    mp_id = get_manufacturer_profile_id()
    machine = _owned_machine(machine_id, mp_id)
    if not machine:
        flash("Machine not found.", "error")
        return redirect(url_for("manufacturer.machines"))

    processes, materials = _load_lookups()
    caps = db.session.execute(
        db.text(
            """SELECT c.capability_id, c.material_id, c.max_quantity, mt.name AS material_name
               FROM machine_capabilities c
               LEFT JOIN materials mt ON mt.material_id = c.material_id
               WHERE c.machine_id = :mid"""
        ),
        {"mid": machine_id},
    ).mappings().all()
    existing_capabilities = [dict(c) for c in caps]

    if request.method == "GET":
        selected_process = request.args.get("process_id") or machine.get("process_id")
        return machine_form_page(
            page_title="Edit Machine",
            machine=dict(machine),
            processes=processes,
            materials=_materials_for_process(materials, selected_process),
            existing_capabilities=existing_capabilities,
            form={
                "machine_name": machine.get("machine_name") or "",
                "process_id": selected_process,
                "max_dimensions": machine.get("max_dimensions") or "",
                "is_active": "true" if machine.get("is_active") else "false",
            },
        )

    if request.form.get("action") == "refresh_materials":
        return redirect(
            url_for(
                "manufacturer.machine_edit",
                machine_id=machine_id,
                process_id=request.form.get("process_id"),
            )
        )

    machine_name = request.form.get("machine_name", "").strip()
    if not machine_name:
        flash("Machine name is required.", "error")
        return redirect(url_for("manufacturer.machine_edit", machine_id=machine_id))

    is_active = request.form.get("is_active") == "true"
    db.session.execute(
        db.text(
            """UPDATE machines SET
               machine_name=:name,
               process_id=:pid,
               max_dimensions=:dims,
               is_active=:active
               WHERE machine_id=:mid"""
        ),
        {
            "name": machine_name,
            "pid": request.form.get("process_id"),
            "dims": request.form.get("max_dimensions"),
            "active": is_active,
            "mid": machine_id,
        },
    )
    db.session.commit()
    flash("Machine updated.", "success")
    return redirect(url_for("manufacturer.machines"))


@manufacturer_bp.route("/machines/<int:machine_id>/delete", methods=["POST"])
@role_required("manufacturer")
@_require_approved_manufacturer
def machine_delete(machine_id):
    mp_id = get_manufacturer_profile_id()
    if not _owned_machine(machine_id, mp_id):
        flash("Machine not found.", "error")
        return redirect(url_for("manufacturer.machines"))

    db.session.execute(db.text("DELETE FROM machine_capabilities WHERE machine_id=:mid"), {"mid": machine_id})
    db.session.execute(db.text("DELETE FROM machines WHERE machine_id=:mid"), {"mid": machine_id})
    db.session.commit()
    flash("Machine deleted.", "success")
    return redirect(url_for("manufacturer.machines"))


@manufacturer_bp.route("/machines/<int:machine_id>/capabilities/add", methods=["POST"])
@role_required("manufacturer")
@_require_approved_manufacturer
def add_capability(machine_id):
    mp_id = get_manufacturer_profile_id()
    if not _owned_machine(machine_id, mp_id):
        flash("Machine not found.", "error")
        return redirect(url_for("manufacturer.machines"))

    material_id = request.form.get("material_id")
    if not material_id:
        flash("Material is required.", "error")
        return redirect(url_for("manufacturer.machine_edit", machine_id=machine_id))

    db.session.execute(
        db.text(
            """INSERT INTO machine_capabilities (machine_id, material_id, max_quantity)
               VALUES (:mid, :matid, :mq)"""
        ),
        {
            "mid": machine_id,
            "matid": material_id,
            "mq": request.form.get("max_quantity") or 1000,
        },
    )
    db.session.commit()
    flash("Capability added.", "success")
    return redirect(url_for("manufacturer.machine_edit", machine_id=machine_id))


@manufacturer_bp.route("/capabilities/<int:capability_id>/delete", methods=["POST"])
@role_required("manufacturer")
@_require_approved_manufacturer
def delete_capability(capability_id):
    mp_id = get_manufacturer_profile_id()
    owner = db.session.execute(
        db.text(
            """SELECT c.machine_id FROM machine_capabilities c
               JOIN machines m ON m.machine_id = c.machine_id
               WHERE c.capability_id=:cid AND m.manufacturer_profile_id=:mp"""
        ),
        {"cid": capability_id, "mp": mp_id},
    ).first()
    if not owner:
        flash("Capability not found.", "error")
        return redirect(url_for("manufacturer.machines"))

    machine_id = owner[0]
    db.session.execute(
        db.text("DELETE FROM machine_capabilities WHERE capability_id=:cid"),
        {"cid": capability_id},
    )
    db.session.commit()
    flash("Capability removed.", "success")
    return redirect(url_for("manufacturer.machine_edit", machine_id=machine_id))


@manufacturer_bp.route("/available-requests")
@role_required("manufacturer")
@_require_approved_manufacturer
def available_requests():
    mp_id = get_manufacturer_profile_id()
    rows = db.session.execute(
        db.text(
            """SELECT o.order_id, o.status, o.created_at, o.machine_id,
               r.quantity, r.surface_finish, r.notes, r.estimated_days,
               p.name AS process_name, mt.name AS material_name,
               uf.filename
               FROM orders o
               JOIN manufacturing_requests r ON r.request_id = o.request_id
               LEFT JOIN manufacturing_processes p ON p.process_id = r.process_id
               LEFT JOIN materials mt ON mt.material_id = r.material_id
               LEFT JOIN uploaded_files uf ON uf.file_id = r.file_id
               WHERE o.manufacturer_profile_id = :mp AND o.status = 'Request Submitted'
               ORDER BY o.created_at DESC"""
        ),
        {"mp": mp_id},
    ).mappings().all()

    requests_list = [dict(r) for r in rows]
    requests_list, used_fallback = order_requests_by_priority(requests_list)

    return available_requests_page(
        requests=requests_list,
        used_fallback=used_fallback,
    )


@manufacturer_bp.route("/available-requests/<int:order_id>/accept", methods=["POST"])
@role_required("manufacturer")
@_require_approved_manufacturer
def accept_order(order_id):
    mp_id = get_manufacturer_profile_id()
    order = _get_owned_order(order_id, mp_id)
    if not order:
        flash("Order not found.", "error")
        return redirect(url_for("manufacturer.available_requests"))
    if order["status"] != "Request Submitted":
        flash(f"Cannot accept order in status '{order['status']}'.", "error")
        return redirect(url_for("manufacturer.available_requests"))

    db.session.execute(
        db.text("UPDATE orders SET status='Accepted', updated_at=now() WHERE order_id=:oid"),
        {"oid": order_id},
    )
    db.session.execute(
        db.text(
            """INSERT INTO order_status_history (order_id, status, changed_by, remarks)
               VALUES (:oid, 'Accepted', :uid, 'Order accepted by manufacturer')"""
        ),
        {"oid": order_id, "uid": session["user_id"]},
    )
    notify_order_customer(
        order_id,
        f"Order #{order_id} Accepted",
        f"Your manufacturing request was accepted by the manufacturer and is now in production.",
    )
    db.session.commit()
    flash("Order accepted.", "success")
    return redirect(url_for("manufacturer.available_requests"))


@manufacturer_bp.route("/available-requests/<int:order_id>/reject", methods=["GET", "POST"])
@role_required("manufacturer")
@_require_approved_manufacturer
def reject_order(order_id):
    mp_id = get_manufacturer_profile_id()
    order = _get_owned_order(order_id, mp_id)
    if not order:
        flash("Order not found.", "error")
        return redirect(url_for("manufacturer.available_requests"))
    if order["status"] != "Request Submitted":
        flash(f"Cannot reject order in status '{order['status']}'.", "error")
        return redirect(url_for("manufacturer.available_requests"))

    if request.method == "GET":
        return reject_order_page(
            order_id=order_id,
        )

    reason = request.form.get("reason", "").strip() or "Order rejected by manufacturer"
    db.session.execute(
        db.text("UPDATE orders SET status='Cancelled', updated_at=now() WHERE order_id=:oid"),
        {"oid": order_id},
    )
    db.session.execute(
        db.text(
            """INSERT INTO order_status_history (order_id, status, changed_by, remarks)
               VALUES (:oid, 'Cancelled', :uid, :remarks)"""
        ),
        {"oid": order_id, "uid": session["user_id"], "remarks": reason},
    )
    notify_order_customer(
        order_id,
        f"Order #{order_id} Rejected",
        f"Your manufacturing request was rejected by the manufacturer. Reason: {reason}",
    )
    db.session.commit()
    flash("Order rejected.", "success")
    return redirect(url_for("manufacturer.available_requests"))


@manufacturer_bp.route("/active-orders")
@role_required("manufacturer")
@_require_approved_manufacturer
def active_orders():
    mp_id = get_manufacturer_profile_id()
    rows = db.session.execute(
        db.text(
            """SELECT o.order_id, o.status, o.created_at, o.updated_at,
               r.quantity, p.name AS process_name, mt.name AS material_name
               FROM orders o
               JOIN manufacturing_requests r ON r.request_id = o.request_id
               LEFT JOIN manufacturing_processes p ON p.process_id = r.process_id
               LEFT JOIN materials mt ON mt.material_id = r.material_id
               WHERE o.manufacturer_profile_id = :mp AND o.status IN ('Accepted', 'Manufacturing', 'Quality Check')
               ORDER BY o.updated_at DESC"""
        ),
        {"mp": mp_id},
    ).mappings().all()

    orders = []
    for row in rows:
        item = dict(row)
        item["next_status"] = NEXT_STATUS.get(item["status"])
        orders.append(item)

    return active_orders_page(
        orders=orders,
    )


@manufacturer_bp.route("/active-orders/<int:order_id>/advance", methods=["GET", "POST"])
@role_required("manufacturer")
@_require_approved_manufacturer
def advance_order(order_id):
    mp_id = get_manufacturer_profile_id()
    order = _get_owned_order(order_id, mp_id)
    if not order:
        flash("Order not found.", "error")
        return redirect(url_for("manufacturer.active_orders"))

    next_status = NEXT_STATUS.get(order["status"])
    if not next_status:
        flash(f"Cannot advance order in status '{order['status']}'.", "error")
        return redirect(url_for("manufacturer.active_orders"))

    customer_price = order.get("customer_price") if next_status == "Completed" else None
    maximum_price = manufacturer_price_limit(customer_price)

    if request.method == "GET":
        return advance_order_page(
            order_id=order_id,
            current_status=order["status"],
            next_status=next_status,
            customer_price=customer_price,
            maximum_price=maximum_price,
        )

    remarks = request.form.get("remarks", "").strip() or f"Status updated to {next_status}"
    fields = {"oid": order_id, "status": next_status}
    extra_set = ""
    if next_status == "Completed":
        final_cost_raw = request.form.get("final_cost", "").strip()
        if not final_cost_raw:
            flash("A manufacturer quote is required before completing this order.", "error")
            return redirect(url_for("manufacturer.advance_order", order_id=order_id))
        final_cost = parse_price(final_cost_raw)
        if maximum_price is None or not valid_manufacturer_quote(customer_price, final_cost):
            if maximum_price is None:
                message = "A saved customer price is unavailable, so a manufacturer quote cannot be submitted."
            else:
                message = f"Enter a valid quote no greater than {format_cost(maximum_price)} (75% of the customer price)."
            flash(message, "error")
            return redirect(url_for("manufacturer.advance_order", order_id=order_id))
        fields["fc"] = final_cost
        extra_set = ", final_cost=:fc"

    db.session.execute(
        db.text(f"UPDATE orders SET status=:status, updated_at=now(){extra_set} WHERE order_id=:oid"),
        fields,
    )
    db.session.execute(
        db.text(
            """INSERT INTO order_status_history (order_id, status, changed_by, remarks)
               VALUES (:oid, :status, :uid, :remarks)"""
        ),
        {"oid": order_id, "status": next_status, "uid": session["user_id"], "remarks": remarks},
    )
    notify_order_customer(
        order_id,
        f"Order #{order_id} {next_status}",
        f"Order #{order_id} advanced to status '{next_status}'. Remarks: {remarks}",
    )
    db.session.commit()
    flash("Order status updated.", "success")
    return redirect(url_for("manufacturer.active_orders"))


@manufacturer_bp.route("/completed-orders")
@role_required("manufacturer")
@_require_approved_manufacturer
def completed_orders():
    mp_id = get_manufacturer_profile_id()
    rows = db.session.execute(
        db.text(
            """SELECT o.order_id, o.status, o.created_at, o.updated_at, o.final_cost,
               r.quantity, p.name AS process_name, mt.name AS material_name
               FROM orders o
               JOIN manufacturing_requests r ON r.request_id = o.request_id
               LEFT JOIN manufacturing_processes p ON p.process_id = r.process_id
               LEFT JOIN materials mt ON mt.material_id = r.material_id
               WHERE o.manufacturer_profile_id = :mp AND o.status = 'Completed'
               ORDER BY o.updated_at DESC"""
        ),
        {"mp": mp_id},
    ).mappings().all()

    return completed_orders_page(
        orders=[dict(r) for r in rows],
    )
