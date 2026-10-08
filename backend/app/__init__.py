import os
from datetime import datetime
from flask import Flask, redirect, url_for, request, session
from app.config import Config
from app.extensions import db, bcrypt
from app.models.user import User
from app.pyui.misc_pages import (
    landing_page,
    about_page,
    not_found_page,
    server_error_page,
)

APP_DIR = os.path.dirname(os.path.abspath(__file__))


def create_app():
    app = Flask(
        __name__,
        static_folder=os.path.join(APP_DIR, "static"),
        static_url_path="/static",
    )
    app.config.from_object(Config)
    db.init_app(app)
    bcrypt.init_app(app)

    @app.errorhandler(404)
    def not_found_error(error):
        return not_found_page(session_role=session.get("role")), 404

    @app.errorhandler(500)
    def internal_error(error):
        original = getattr(error, "original_exception", None) or error
        app.logger.error(
            "Unhandled request error (%s %s): %s",
            request.method,
            request.path,
            original,
            exc_info=(type(original), original, original.__traceback__),
        )
        db.session.rollback()
        return server_error_page(session_role=session.get("role")), 500

    with app.app_context():
        db.session.execute(
            db.text(
                """
                CREATE TABLE IF NOT EXISTS notifications (
                    notification_id SERIAL PRIMARY KEY,
                    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    is_read BOOLEAN DEFAULT FALSE
                )
                """
            )
        )
        db.session.commit()

    @app.context_processor
    def inject_globals():
        user = None
        if "user_id" in session:
            user = User.query.get(session["user_id"])
        return dict(current_user=user)

    @app.template_filter("format_date")
    def format_date(value):
        if not value:
            return "—"
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return str(value)

    @app.template_filter("format_datetime")
    def format_datetime(value):
        if not value:
            return "—"
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M")
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            return str(value)

    @app.template_filter("format_cost")
    def format_cost(value):
        if value is None:
            return "—"
        try:
            num = float(value)
        except (TypeError, ValueError):
            return "—"
        return f"₹{num:,.2f}"

    @app.route("/")
    def index():
        if "user_id" not in session:
            return landing_page()
        role = session.get("role")
        if role == "customer":
            return redirect(url_for("customer.dashboard"))
        if role == "manufacturer":
            return redirect(url_for("manufacturer.dashboard"))
        if role == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("auth.login"))

    @app.route("/about")
    def about():
        return about_page()

    from app.routes.auth_routes import auth_bp
    from app.routes.customer_routes import customer_bp
    from app.routes.manufacturer_routes import manufacturer_bp
    from app.routes.admin_routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(manufacturer_bp)
    app.register_blueprint(admin_bp)

    return app
