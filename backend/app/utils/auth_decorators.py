from functools import wraps
from flask import session, redirect, url_for, request, flash


def _redirect_for_role(role):
    if role == "customer":
        return redirect(url_for("customer.dashboard"))
    if role == "manufacturer":
        return redirect(url_for("manufacturer.dashboard"))
    if role == "admin":
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("auth.login"))


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return wrapper


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("auth.login", next=request.url))
            if session.get("role") not in roles:
                flash("You do not have permission to access that page.", "error")
                return _redirect_for_role(session.get("role"))
            return f(*args, **kwargs)
        return wrapper
    return decorator
