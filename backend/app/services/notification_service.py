from app.extensions import db


def notify_user(user_id, subject, message):
    if user_id is None:
        return None

    row = db.session.execute(
        db.text("SELECT email FROM users WHERE user_id=:uid"),
        {"uid": user_id},
    ).first()
    email = row[0] if row else "unknown@local"

    print(f"[NOTIFICATION] To: {email} | Subject: {subject} | Message: {message}")

    db.session.execute(
        db.text(
            """
            INSERT INTO notifications (user_id, message, is_read)
            VALUES (:uid, :message, FALSE)
            """
        ),
        {"uid": user_id, "message": f"{subject}: {message}"},
    )
    return {"user_id": user_id, "email": email, "subject": subject, "message": message}


def notify_order_customer(order_id, subject, message):
    row = db.session.execute(
        db.text(
            """
            SELECT u.user_id, u.email
            FROM orders o
            JOIN manufacturing_requests mr ON mr.request_id = o.request_id
            JOIN customer_profiles cp ON cp.customer_profile_id = mr.customer_profile_id
            JOIN users u ON u.user_id = cp.user_id
            WHERE o.order_id = :oid
            """
        ),
        {"oid": order_id},
    ).first()

    if not row:
        return None

    return notify_user(row[0], subject, message)


def notify_manufacturer_profile(user_id, subject, message):
    return notify_user(user_id, subject, message)
