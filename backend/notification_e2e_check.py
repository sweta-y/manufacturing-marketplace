from app import create_app
from app.extensions import db
import contextlib
from io import StringIO


def fetch_order_for_manufacturer(manufacturer_profile_id):
    return db.session.execute(
        db.text(
            """
            SELECT order_id
            FROM orders
            WHERE manufacturer_profile_id = :mp AND status = 'Request Submitted'
            ORDER BY order_id ASC
            LIMIT 1
            """
        ),
        {"mp": manufacturer_profile_id},
    ).first()


def fetch_pending_manufacturer():
    return db.session.execute(
        db.text(
            """
            SELECT mp.manufacturer_profile_id, u.user_id, u.email
            FROM manufacturer_profiles mp
            JOIN users u ON u.user_id = mp.user_id
            WHERE mp.approval_status = 'pending'
            ORDER BY mp.manufacturer_profile_id ASC
            LIMIT 1
            """
        )
    ).first()


app = create_app()
app.config["WTF_CSRF_ENABLED"] = False

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

    manufacturer = db.session.execute(
        db.text(
            """
            SELECT mp.manufacturer_profile_id, u.user_id, u.email
            FROM manufacturer_profiles mp
            JOIN users u ON u.user_id = mp.user_id
            WHERE u.email = :email
            LIMIT 1
            """
        ),
        {"email": "james.morrison@precisioncnc.com"},
    ).first()

    if not manufacturer:
        raise RuntimeError("Manufacturer seed user not found")

    order = fetch_order_for_manufacturer(manufacturer[0])
    if not order:
        raise RuntimeError("No request-submitted order found for manufacturer")

    with app.test_client() as client:
        client.get("/logout", follow_redirects=True)
        login_res = client.post(
            "/login",
            data={"email": "james.morrison@precisioncnc.com", "password": "Password123!"},
            follow_redirects=False,
        )
        print("LOGIN_MANUFACTURER", login_res.status_code)

        buffer = StringIO()
        with contextlib.redirect_stdout(buffer):
            accept_res = client.post(f"/manufacturer/available-requests/{order[0]}/accept", follow_redirects=False)
        print("ACCEPT_STATUS", accept_res.status_code)
        print(buffer.getvalue().strip())

        print("NOTIFICATIONS_AFTER_ACCEPT")
        notif_rows = db.session.execute(
            db.text(
                """
                SELECT notification_id, user_id, message, created_at, is_read
                FROM notifications
                ORDER BY notification_id DESC
                LIMIT 10
                """
            )
        ).fetchall()
        for row in notif_rows:
            print(row)

        pending = fetch_pending_manufacturer()
        if not pending:
            raise RuntimeError("No pending manufacturer profile found for admin approval test")

        client.get("/logout", follow_redirects=True)
        admin_login = client.post(
            "/login",
            data={"email": "admin@marketplace.com", "password": "Password123!"},
            follow_redirects=False,
        )
        print("LOGIN_ADMIN", admin_login.status_code)

        buffer = StringIO()
        with contextlib.redirect_stdout(buffer):
            approve_res = client.post(f"/admin/manufacturer-approvals/{pending[0]}/approve", follow_redirects=False)
        print("APPROVE_STATUS", approve_res.status_code)
        print(buffer.getvalue().strip())

        print("NOTIFICATIONS_AFTER_APPROVE")
        notif_rows = db.session.execute(
            db.text(
                """
                SELECT notification_id, user_id, message, created_at, is_read
                FROM notifications
                ORDER BY notification_id DESC
                LIMIT 10
                """
            )
        ).fetchall()
        for row in notif_rows:
            print(row)
