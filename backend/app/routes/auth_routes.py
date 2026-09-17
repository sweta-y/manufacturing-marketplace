from flask import Blueprint, request, redirect, url_for, session, flash
from app.extensions import db, bcrypt
from app.models.user import User
from app.utils.auth_decorators import login_required
from app.pyui.auth_pages import login_page, register_page, register_manufacturer_page
from app.services.supabase_client import supabase_sign_in, supabase_sign_up


auth_bp = Blueprint("auth", __name__)


def _redirect_after_login(user):
    if user.role == "customer":
        return redirect(url_for("customer.dashboard"))
    if user.role == "manufacturer":
        profile = db.session.execute(
            db.text("SELECT approval_status FROM manufacturer_profiles WHERE user_id = :uid"),
            {"uid": user.user_id},
        ).scalar()
        if profile in ("pending", "rejected"):
            return redirect(url_for("manufacturer.status_page"))
        return redirect(url_for("manufacturer.dashboard"))
    if user.role == "admin":
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if "user_id" in session:
            return _redirect_after_login(User.query.get(session["user_id"]))
        return login_page(next_url=request.args.get("next"), email="")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    next_url = request.form.get("next")

    supabase_ok, supabase_data = supabase_sign_in(email, password)
    user = None
    if supabase_ok:
        supabase_uid = supabase_data["id"]
        user = User.query.filter_by(supabase_uid=supabase_uid).first()
        if not user:
            user = User.query.filter_by(email=email).first()
            if user and not user.supabase_uid:
                user.supabase_uid = supabase_uid
                db.session.commit()
        if not user:
            flash("Supabase login succeeded, but local account setup is incomplete.", "error")
            return login_page(next_url=next_url, email=email), 401
    else:
        # Backward compatibility for seed accounts that only have local bcrypt hashes.
        user = User.query.filter_by(email=email).first()
        if not user or not user.password_hash or not bcrypt.check_password_hash(user.password_hash, password):
            flash("Invalid email or password.", "error")
            return login_page(next_url=next_url, email=email), 401

    if not user:
        flash("Invalid email or password.", "error")
        return login_page(next_url=next_url, email=email), 401

    if not user.is_active:
        flash("Account inactive.", "error")
        return login_page(next_url=next_url, email=email), 403

    session["user_id"] = user.user_id
    session["role"] = user.role
    flash("Login successful.", "success")

    if next_url:
        return redirect(next_url)
    return _redirect_after_login(user)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return register_page(form={})

    form = {
        "full_name": request.form.get("full_name", "").strip(),
        "email": request.form.get("email", "").strip(),
        "phone": request.form.get("phone", "").strip(),
    }
    password = request.form.get("password", "")

    if not all([form["full_name"], form["email"], password]):
        flash("Missing required fields.", "error")
        return register_page(form=form), 400

    if User.query.filter_by(email=form["email"]).first():
        flash("Email already registered.", "error")
        return register_page(form=form), 400

    supabase_ok, supabase_data = supabase_sign_up(form["email"], password)
    if not supabase_ok:
        flash(f"Registration failed: {supabase_data}", "error")
        return register_page(form=form), 400

    user = User(
        email=form["email"],
        password_hash=None,
        supabase_uid=supabase_data["id"],
        role="customer",
        full_name=form["full_name"],
        phone=form["phone"] or None,
    )
    db.session.add(user)
    db.session.commit()
    db.session.execute(
        db.text("INSERT INTO customer_profiles (user_id) VALUES (:uid)"),
        {"uid": user.user_id},
    )
    db.session.commit()

    if not supabase_data.get("email_confirmed", True):
        flash("Registered successfully. Confirm your email before logging in.", "success")
        return redirect(url_for("auth.login"))

    session["user_id"] = user.user_id
    session["role"] = user.role
    flash("Registered successfully.", "success")
    return _redirect_after_login(user)


@auth_bp.route("/register-manufacturer", methods=["GET", "POST"])
def register_manufacturer():
    if request.method == "GET":
        return register_manufacturer_page(form={})

    form = {
        "full_name": request.form.get("full_name", "").strip(),
        "business_name": request.form.get("business_name", "").strip(),
        "email": request.form.get("email", "").strip(),
        "phone": request.form.get("phone", "").strip(),
    }
    password = request.form.get("password", "")

    if not all([form["full_name"], form["business_name"], form["email"], password]):
        flash("Missing required fields.", "error")
        return register_manufacturer_page(form=form), 400

    if User.query.filter_by(email=form["email"]).first():
        flash("Email already registered.", "error")
        return register_manufacturer_page(form=form), 400

    supabase_ok, supabase_data = supabase_sign_up(form["email"], password)
    if not supabase_ok:
        flash(f"Registration failed: {supabase_data}", "error")
        return register_manufacturer_page(form=form), 400

    user = User(
        email=form["email"],
        password_hash=None,
        supabase_uid=supabase_data["id"],
        role="manufacturer",
        full_name=form["full_name"],
        phone=form["phone"] or None,
    )
    db.session.add(user)
    db.session.commit()
    db.session.execute(
        db.text(
            "INSERT INTO manufacturer_profiles (user_id, business_name, approval_status) "
            "VALUES (:uid, :bname, 'pending')"
        ),
        {"uid": user.user_id, "bname": form["business_name"]},
    )
    db.session.commit()

    if not supabase_data.get("email_confirmed", True):
        flash("Manufacturer registered. Confirm your email before logging in.", "success")
        return redirect(url_for("auth.login"))

    session["user_id"] = user.user_id
    session["role"] = user.role
    flash("Manufacturer registered — pending approval.", "success")
    return _redirect_after_login(user)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("auth.login"))
