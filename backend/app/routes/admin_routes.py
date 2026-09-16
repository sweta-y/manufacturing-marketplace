from flask import Blueprint, request, redirect, url_for, flash
from app.extensions import db
from app.services.notification_service import notify_user
from app.utils.auth_decorators import role_required
from app.pyui.admin_pages import (
    dashboard_page,
    users_page,
    user_detail_page,
    machines_page,
    orders_page,
    order_detail_page,
    reports_page,
    manufacturer_approvals_page,
)


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _status_for_user(row):
    role = row["role"]
    if role == "manufacturer":
        return row["approval_status"] or "approved"
    return "active" if row["is_active"] else "inactive"


@admin_bp.route("/dashboard")
@role_required("admin")
def dashboard():
    return dashboard_page()


@admin_bp.route("/users")
@role_required("admin")
def users():
    role_filter = request.args.get("role", "all")
    where = []
    params = {}
    if role_filter != "all":
        where.append("u.role = :role")
        params["role"] = role_filter

    query = """
        SELECT u.user_id, u.full_name, u.email, u.role, u.created_at, u.is_active,
               mp.manufacturer_profile_id, mp.approval_status,
               cp.customer_profile_id
        FROM users u
        LEFT JOIN manufacturer_profiles mp ON mp.user_id = u.user_id
        LEFT JOIN customer_profiles cp ON cp.user_id = u.user_id
    """
    if where:
        query += " WHERE " + " AND ".join(where)
    query += " ORDER BY u.created_at DESC"

    rows = db.session.execute(db.text(query), params).mappings().all()
    users_list = []
    for row in rows:
        users_list.append({
            "user_id": row["user_id"],
            "full_name": row["full_name"],
            "email": row["email"],
            "role": row["role"],
            "created_at": row["created_at"],
            "status": _status_for_user(row),
        })

    return users_page(
        users=users_list,
        role_filter=role_filter,
    )


@admin_bp.route("/users/<int:user_id>")
@role_required("admin")
def user_detail(user_id):
    user = db.session.execute(
        db.text(
            """
            SELECT u.user_id, u.full_name, u.email, u.role, u.phone, u.created_at, u.is_active,
                   mp.manufacturer_profile_id, mp.business_name, mp.address AS manufacturer_address,
                   mp.approval_status, mp.rejection_reason,
                   cp.customer_profile_id, cp.company_name, cp.address AS customer_address
            FROM users u
            LEFT JOIN manufacturer_profiles mp ON mp.user_id = u.user_id
            LEFT JOIN customer_profiles cp ON cp.user_id = u.user_id
            WHERE u.user_id = :uid
            """
        ),
        {"uid": user_id},
    ).mappings().first()

    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin.users"))

    manufacturer_orders = []
    manufacturer_machines = []
    customer_orders = []

    if user["role"] == "manufacturer":
        manufacturer_machines = db.session.execute(
            db.text(
                """
                SELECT m.machine_id, m.machine_name, p.name AS process_name, m.is_active
                FROM machines m
                LEFT JOIN manufacturing_processes p ON p.process_id = m.process_id
                WHERE m.manufacturer_profile_id = :mp
                ORDER BY m.created_at DESC
                """
            ),
            {"mp": user["manufacturer_profile_id"]},
        ).mappings().all()

        manufacturer_orders = db.session.execute(
            db.text(
                """
                SELECT o.order_id, o.status, o.created_at,
                       cu.full_name AS customer_name
                FROM orders o
                JOIN manufacturing_requests mr ON mr.request_id = o.request_id
                JOIN customer_profiles cp ON cp.customer_profile_id = mr.customer_profile_id
                JOIN users cu ON cu.user_id = cp.user_id
                WHERE o.manufacturer_profile_id = :mp
                ORDER BY o.created_at DESC
                """
            ),
            {"mp": user["manufacturer_profile_id"]},
        ).mappings().all()

    if user["role"] == "customer":
        customer_orders = db.session.execute(
            db.text(
                """
                SELECT o.order_id, o.status, o.created_at,
                       mp.business_name AS manufacturer_name
                FROM orders o
                JOIN manufacturing_requests mr ON mr.request_id = o.request_id
                JOIN manufacturer_profiles mp ON mp.manufacturer_profile_id = o.manufacturer_profile_id
                WHERE mr.customer_profile_id = :cp
                ORDER BY o.created_at DESC
                """
            ),
            {"cp": user["customer_profile_id"]},
        ).mappings().all()

    return user_detail_page(
        user=dict(user),
        manufacturer_machines=[dict(r) for r in manufacturer_machines],
        manufacturer_orders=[dict(r) for r in manufacturer_orders],
        customer_orders=[dict(r) for r in customer_orders],
    )


@admin_bp.route("/machines")
@role_required("admin")
def machines():
    process_filter = request.args.get("process_id", "all")
    manufacturer_filter = request.args.get("manufacturer_id", "all")
    where = []
    params = {}

    if process_filter != "all":
        where.append("m.process_id = :process_id")
        params["process_id"] = process_filter
    if manufacturer_filter != "all":
        where.append("m.manufacturer_profile_id = :manufacturer_id")
        params["manufacturer_id"] = manufacturer_filter

    query = """
        SELECT m.machine_id, m.machine_name, m.is_active,
               p.name AS process_name,
               mp.business_name AS manufacturer_name,
               mp.manufacturer_profile_id
        FROM machines m
        LEFT JOIN manufacturing_processes p ON p.process_id = m.process_id
        LEFT JOIN manufacturer_profiles mp ON mp.manufacturer_profile_id = m.manufacturer_profile_id
    """
    if where:
        query += " WHERE " + " AND ".join(where)
    query += " ORDER BY m.created_at DESC"

    rows = db.session.execute(db.text(query), params).mappings().all()
    processes = db.session.execute(db.text("SELECT process_id, name FROM manufacturing_processes ORDER BY name")).mappings().all()
    manufacturers = db.session.execute(
        db.text(
            """
            SELECT mp.manufacturer_profile_id, mp.business_name
            FROM manufacturer_profiles mp
            JOIN users u ON u.user_id = mp.user_id
            ORDER BY mp.business_name
            """
        )
    ).mappings().all()

    return machines_page(
        machines=[dict(r) for r in rows],
        processes=[dict(p) for p in processes],
        manufacturers=[dict(m) for m in manufacturers],
        process_filter=process_filter,
        manufacturer_filter=manufacturer_filter,
    )


@admin_bp.route("/orders")
@role_required("admin")
def orders():
    status_filter = request.args.get("status", "all")
    where = []
    params = {}
    if status_filter != "all":
        where.append("o.status = :status")
        params["status"] = status_filter

    query = """
        SELECT o.order_id, o.status, o.created_at,
               cu.full_name AS customer_name,
               mu.full_name AS manufacturer_name,
               mp.business_name AS manufacturer_business_name
        FROM orders o
        JOIN manufacturing_requests mr ON mr.request_id = o.request_id
        JOIN customer_profiles cp ON cp.customer_profile_id = mr.customer_profile_id
        JOIN users cu ON cu.user_id = cp.user_id
        LEFT JOIN manufacturer_profiles mp ON mp.manufacturer_profile_id = o.manufacturer_profile_id
        LEFT JOIN users mu ON mu.user_id = mp.user_id
    """
    if where:
        query += " WHERE " + " AND ".join(where)
    query += " ORDER BY o.created_at DESC"

    rows = db.session.execute(db.text(query), params).mappings().all()
    statuses = db.session.execute(
        db.text("SELECT DISTINCT status FROM orders ORDER BY status")
    ).fetchall()

    return orders_page(
        orders=[dict(r) for r in rows],
        statuses=[row[0] for row in statuses],
        status_filter=status_filter,
    )


@admin_bp.route("/orders/<int:order_id>")
@role_required("admin")
def order_detail(order_id):
    order = db.session.execute(
        db.text(
            """
            SELECT o.order_id, o.status, o.created_at, o.updated_at, o.final_cost,
                   mp.business_name, mp.manufacturer_profile_id,
                   r.quantity, r.surface_finish, r.notes,
                   p.name AS process_name, mt.name AS material_name,
                   cu.full_name AS customer_name, cu.email AS customer_email,
                   mu.full_name AS manufacturer_contact_name
            FROM orders o
            JOIN manufacturing_requests r ON r.request_id = o.request_id
            JOIN customer_profiles cp ON cp.customer_profile_id = r.customer_profile_id
            JOIN users cu ON cu.user_id = cp.user_id
            LEFT JOIN manufacturer_profiles mp ON mp.manufacturer_profile_id = o.manufacturer_profile_id
            LEFT JOIN users mu ON mu.user_id = mp.user_id
            LEFT JOIN manufacturing_processes p ON p.process_id = r.process_id
            LEFT JOIN materials mt ON mt.material_id = r.material_id
            WHERE o.order_id = :oid
            """
        ),
        {"oid": order_id},
    ).mappings().first()

    if not order:
        flash("Order not found.", "error")
        return redirect(url_for("admin.orders"))

    history = db.session.execute(
        db.text(
            """
            SELECT status, changed_at, remarks, changed_by,
                   (SELECT full_name FROM users WHERE user_id = changed_by) AS changed_by_name
            FROM order_status_history
            WHERE order_id = :oid
            ORDER BY changed_at ASC
            """
        ),
        {"oid": order_id},
    ).mappings().all()

    return order_detail_page(
        order=dict(order),
        history=[dict(h) for h in history],
    )


@admin_bp.route("/reports")
@role_required("admin")
def reports():
    total_users = db.session.execute(
        db.text("SELECT role, COUNT(*) AS count FROM users GROUP BY role ORDER BY role")
    ).mappings().all()

    orders_by_status = db.session.execute(
        db.text("SELECT status, COUNT(*) AS count FROM orders GROUP BY status ORDER BY status")
    ).mappings().all()

    machine_counts = db.session.execute(
        db.text(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN is_active = TRUE THEN 1 ELSE 0 END) AS active,
                SUM(CASE WHEN is_active = FALSE THEN 1 ELSE 0 END) AS inactive
            FROM machines
            """
        )
    ).mappings().first()

    pending_approvals = db.session.execute(
        db.text("SELECT COUNT(*) AS count FROM manufacturer_profiles WHERE approval_status = 'pending'")
    ).scalar() or 0

    recent_7_days = db.session.execute(
        db.text("SELECT COUNT(*) AS count FROM orders WHERE created_at >= NOW() - INTERVAL '7 days'")
    ).scalar() or 0

    recent_30_days = db.session.execute(
        db.text("SELECT COUNT(*) AS count FROM orders WHERE created_at >= NOW() - INTERVAL '30 days'")
    ).scalar() or 0

    return reports_page(
        total_users=[dict(r) for r in total_users],
        orders_by_status=[dict(r) for r in orders_by_status],
        machine_counts=dict(machine_counts) if machine_counts else {"total": 0, "active": 0, "inactive": 0},
        pending_approvals=pending_approvals,
        recent_7_days=recent_7_days,
        recent_30_days=recent_30_days,
    )


@admin_bp.route("/manufacturer-approvals")
@role_required("admin")
def manufacturer_approvals():
    rows = db.session.execute(
        db.text(
            """
            SELECT mp.manufacturer_profile_id, mp.business_name, mp.created_at, mp.rejection_reason,
                   u.email, u.full_name
            FROM manufacturer_profiles mp
            JOIN users u ON u.user_id = mp.user_id
            WHERE mp.approval_status = 'pending'
            ORDER BY mp.created_at DESC
            """
        )
    ).mappings().all()

    return manufacturer_approvals_page(
        approvals=[dict(r) for r in rows],
    )


@admin_bp.route("/manufacturer-approvals/<int:manufacturer_profile_id>/approve", methods=["POST"])
@role_required("admin")
def approve_manufacturer(manufacturer_profile_id):
    profile = db.session.execute(
        db.text(
            """
            SELECT u.user_id, u.email
            FROM manufacturer_profiles mp
            JOIN users u ON u.user_id = mp.user_id
            WHERE mp.manufacturer_profile_id = :id
            """
        ),
        {"id": manufacturer_profile_id},
    ).first()

    db.session.execute(
        db.text(
            """
            UPDATE manufacturer_profiles
            SET approval_status = 'approved', rejection_reason = NULL, approved_at = NOW()
            WHERE manufacturer_profile_id = :id
            """
        ),
        {"id": manufacturer_profile_id},
    )
    if profile:
        notify_user(
            profile[0],
            "Manufacturer Registration Approved",
            "Your manufacturer registration was approved by the admin team.",
        )
    db.session.commit()
    flash("Manufacturer approved successfully.", "success")
    return redirect(url_for("admin.manufacturer_approvals"))


@admin_bp.route("/manufacturer-approvals/<int:manufacturer_profile_id>/reject", methods=["POST"])
@role_required("admin")
def reject_manufacturer(manufacturer_profile_id):
    reason = request.form.get("reason", "").strip() or "No reason provided."
    profile = db.session.execute(
        db.text(
            """
            SELECT u.user_id, u.email
            FROM manufacturer_profiles mp
            JOIN users u ON u.user_id = mp.user_id
            WHERE mp.manufacturer_profile_id = :id
            """
        ),
        {"id": manufacturer_profile_id},
    ).first()

    db.session.execute(
        db.text(
            """
            UPDATE manufacturer_profiles
            SET approval_status = 'rejected', rejection_reason = :reason, approved_at = NULL
            WHERE manufacturer_profile_id = :id
            """
        ),
        {"id": manufacturer_profile_id, "reason": reason},
    )
    if profile:
        notify_user(
            profile[0],
            "Manufacturer Registration Rejected",
            f"Your manufacturer registration was rejected. Reason: {reason}",
        )
    db.session.commit()
    flash("Manufacturer rejected.", "success")
    return redirect(url_for("admin.manufacturer_approvals"))
