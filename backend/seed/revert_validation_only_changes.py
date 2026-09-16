"""Revert only the validation/test rows created during E2E checks.

This script intentionally targets only the known validation rows and the six
E2E test users. It does not touch seeded demo data or real customer/manufacturer
accounts.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app
from app.extensions import db
from sqlalchemy import text

TARGET_USER_EMAILS = (
    "testcustomer@test.com",
    "testcustomer@example.com",
    "testmanufacturer@example.com",
    "testmfg@example.com",
    "e2e.customer.d6eb4d7e@test.com",
    "e2e.mfg.eaeb41a2@test.com",
)


def fetch_ids(query, params=None):
    params = params or {}
    rows = db.session.execute(text(query), params).scalars().all()
    return rows


def safe_delete_order_rows(order_ids):
    if not order_ids:
        return
    db.session.execute(text("DELETE FROM order_status_history WHERE order_id IN :ids"), {"ids": tuple(order_ids)})
    db.session.execute(text("DELETE FROM orders WHERE order_id IN :ids"), {"ids": tuple(order_ids)})


with create_app().app_context():
    print("=== BEFORE COUNTS ===")
    for table in ["users", "customer_profiles", "manufacturer_profiles", "machines", "orders", "order_status_history"]:
        count = db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        print(f"{table}: {count}")

    # 1) Restore the real manufacturer name that was intentionally updated during the test flow.
    db.session.execute(text("UPDATE users SET full_name = 'James Morrison' WHERE user_id = 5"))

    # 2) Revert the two explicit validation orders back to their original states.
    db.session.execute(text("DELETE FROM order_status_history WHERE history_id IN (18, 19)"))
    db.session.execute(text("UPDATE orders SET status = 'Request Submitted', final_cost = NULL WHERE order_id = 10"))
    db.session.execute(text("UPDATE orders SET status = 'Manufacturing', final_cost = NULL WHERE order_id = 11"))

    # 3) Remove the validation machine created during E2E testing.
    db.session.execute(text("DELETE FROM machine_capabilities WHERE machine_id = 9"))
    db.session.execute(text("DELETE FROM machines WHERE machine_id = 9"))

    # 4) Remove all data linked to the six validation users, in FK-safe order.
    test_user_ids = fetch_ids(
        "SELECT user_id FROM users WHERE email IN :emails ORDER BY user_id",
        {"emails": TARGET_USER_EMAILS},
    )

    test_customer_profile_ids = fetch_ids(
        "SELECT customer_profile_id FROM customer_profiles WHERE user_id IN :user_ids ORDER BY customer_profile_id",
        {"user_ids": tuple(test_user_ids)} if test_user_ids else {"user_ids": (-1,)},
    )

    test_manufacturer_profile_ids = fetch_ids(
        "SELECT manufacturer_profile_id FROM manufacturer_profiles WHERE user_id IN :user_ids ORDER BY manufacturer_profile_id",
        {"user_ids": tuple(test_user_ids)} if test_user_ids else {"user_ids": (-1,)},
    )

    # Gather any request ids belonging to the validation customer profiles.
    test_request_ids = []
    if test_customer_profile_ids:
        test_request_ids = fetch_ids(
            "SELECT request_id FROM manufacturing_requests WHERE customer_profile_id IN :cp_ids ORDER BY request_id",
            {"cp_ids": tuple(test_customer_profile_ids)},
        )

    test_order_ids = []
    if test_request_ids:
        test_order_ids.extend(
            fetch_ids(
                "SELECT order_id FROM orders WHERE request_id IN :rids ORDER BY order_id",
                {"rids": tuple(test_request_ids)},
            )
        )

    if test_manufacturer_profile_ids:
        test_order_ids.extend(
            fetch_ids(
                "SELECT order_id FROM orders WHERE manufacturer_profile_id IN :mfg_ids ORDER BY order_id",
                {"mfg_ids": tuple(test_manufacturer_profile_ids)},
            )
        )

    # Deduplicate and delete only the validation-specific order chain.
    test_order_ids = sorted(set(test_order_ids))
    safe_delete_order_rows(test_order_ids)

    if test_request_ids:
        db.session.execute(
            text("DELETE FROM manufacturing_requests WHERE request_id IN :rids"),
            {"rids": tuple(test_request_ids)},
        )

    if test_user_ids:
        db.session.execute(
            text("DELETE FROM uploaded_files WHERE user_id IN :user_ids"),
            {"user_ids": tuple(test_user_ids)},
        )

    if test_customer_profile_ids:
        db.session.execute(
            text("DELETE FROM customer_profiles WHERE customer_profile_id IN :cp_ids"),
            {"cp_ids": tuple(test_customer_profile_ids)},
        )

    if test_manufacturer_profile_ids:
        db.session.execute(
            text("DELETE FROM manufacturer_profiles WHERE manufacturer_profile_id IN :mfg_ids"),
            {"mfg_ids": tuple(test_manufacturer_profile_ids)},
        )

    if test_user_ids:
        db.session.execute(
            text("DELETE FROM users WHERE user_id IN :user_ids"),
            {"user_ids": tuple(test_user_ids)},
        )

    db.session.commit()

    print("=== AFTER COUNTS ===")
    for table in ["users", "customer_profiles", "manufacturer_profiles", "machines", "orders", "order_status_history"]:
        count = db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        print(f"{table}: {count}")

    print("=== VALIDATION CHECKS ===")
    print("user_id=5", db.session.execute(text("SELECT user_id, email, full_name FROM users WHERE user_id = 5")).fetchone())
    print("order 10", db.session.execute(text("SELECT order_id, status, final_cost FROM orders WHERE order_id = 10")).fetchone())
    print("order 11", db.session.execute(text("SELECT order_id, status, final_cost FROM orders WHERE order_id = 11")).fetchone())
    print("machine 9", db.session.execute(text("SELECT machine_id, machine_name FROM machines WHERE machine_id = 9")).fetchone())
    print("remaining test users", db.session.execute(
        text("SELECT user_id, email FROM users WHERE email IN :emails ORDER BY user_id"),
        {"emails": TARGET_USER_EMAILS},
    ).fetchall())
