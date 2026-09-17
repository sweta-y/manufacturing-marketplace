import os
import subprocess
from datetime import datetime
from app.extensions import db

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
C_MODULE_DIR = os.path.join(BACKEND_DIR, "c_module")
BIN_NAMES = ["notif_ring.exe", "notif_ring"] if os.name == "nt" else ["notif_ring"]


def _find_binary():
    for name in BIN_NAMES:
        path = os.path.join(C_MODULE_DIR, name)
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
        if os.path.exists(path):
            return path
    return None


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


def get_recent_notifications_via_ring(user_id, limit=5):
    """
    Get user's most recent notifications via the notif_ring circular buffer C binary.
    
    NOTE: The `notifications` table in PostgreSQL remains the permanent source of truth;
    this circular buffer acts as a fast fixed-capacity in-memory "recent view" cache.

    Returns:
        (notifications, used_fallback)
        notifications: list of dicts:
                       [{"notification_id": int, "created_at": datetime/str, "message": str}]
                       (newest first)
        used_fallback: boolean indicating whether SQL fallback was used.
    """
    if not user_id:
        return [], False

    # Fetch all notifications for this user in chronological (ASC) order to push into ring
    rows = db.session.execute(
        db.text(
            """
            SELECT notification_id, created_at, message
            FROM notifications
            WHERE user_id = :uid
            ORDER BY created_at ASC, notification_id ASC
            """
        ),
        {"uid": user_id},
    ).mappings().all()

    if not rows:
        return [], False

    bin_path = _find_binary()
    if not bin_path:
        # Fallback to pure SQL (newest first)
        sql_rows = db.session.execute(
            db.text(
                """
                SELECT notification_id, created_at, message
                FROM notifications
                WHERE user_id = :uid
                ORDER BY created_at DESC, notification_id DESC
                LIMIT :limit
                """
            ),
            {"uid": user_id, "limit": limit},
        ).mappings().all()
        return [dict(r) for r in sql_rows], True

    try:
        total_n = len(rows)
        capacity = max(total_n, 50)
        k = min(limit, total_n)

        # Build stdin protocol
        # CAPACITY
        # N
        # notification_id created_at_epoch message_len
        # message
        # ...
        # K
        lines = [str(capacity), str(total_n)]
        row_map = {}
        for r in rows:
            nid = int(r["notification_id"])
            cat = r["created_at"]
            if isinstance(cat, datetime):
                epoch = int(cat.timestamp())
            else:
                epoch = 0
            msg = str(r["message"]).replace("\r", "").replace("\n", " ")
            msg_bytes = msg.encode("utf-8")
            lines.append(f"{nid} {epoch} {len(msg_bytes)}")
            lines.append(msg)
            row_map[nid] = dict(r)

        lines.append(str(k))
        stdin_data = "\n".join(lines) + "\n"

        proc = subprocess.run(
            [bin_path],
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=5,
        )

        if proc.returncode != 0:
            raise RuntimeError(f"Binary returned {proc.returncode}")

        result = []
        for out_line in proc.stdout.strip().splitlines():
            parts = out_line.strip().split(" ", 2)
            if len(parts) >= 3:
                nid = int(parts[0])
                msg = parts[2]
                orig = row_map.get(nid, {})
                result.append({
                    "notification_id": nid,
                    "created_at": orig.get("created_at"),
                    "message": msg,
                })

        return result, False

    except Exception:
        # SQL fallback
        sql_rows = db.session.execute(
            db.text(
                """
                SELECT notification_id, created_at, message
                FROM notifications
                WHERE user_id = :uid
                ORDER BY created_at DESC, notification_id DESC
                LIMIT :limit
                """
            ),
            {"uid": user_id, "limit": limit},
        ).mappings().all()
        return [dict(r) for r in sql_rows], True
