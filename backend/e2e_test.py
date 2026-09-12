"""End-to-end test of all converted Flask pages and forms."""
import io
import re
import sys
import traceback
from app import create_app
from app.extensions import db

PASSWORD = "Password123!"
USERS = {
    "admin": "admin@marketplace.com",
    "customer": "sarah.chen@acmeindustries.com",
    "manufacturer": "james.morrison@precisioncnc.com",
}

results = []


def record(name, passed, detail=""):
    results.append({"name": name, "passed": passed, "detail": detail})
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {name}" + (f" — {detail}" if detail and not passed else ""))


def login(client, role):
    email = USERS[role]
    r = client.post("/login", data={"email": email, "password": PASSWORD}, follow_redirects=False)
    return r.status_code in (302, 303)


def get_user_id(email):
    row = db.session.execute(db.text("SELECT user_id FROM users WHERE email=:e"), {"e": email}).first()
    return row[0] if row else None


def get_customer_profile_id(user_id):
    row = db.session.execute(
        db.text("SELECT customer_profile_id FROM customer_profiles WHERE user_id=:u"), {"u": user_id}
    ).first()
    return row[0] if row else None


def get_manufacturer_profile_id(user_id):
    row = db.session.execute(
        db.text("SELECT manufacturer_profile_id FROM manufacturer_profiles WHERE user_id=:u"), {"u": user_id}
    ).first()
    return row[0] if row else None


def test_get(client, name, path, marker, role=None):
    if role:
        client.get("/logout", follow_redirects=True)
        if not login(client, role):
            record(name, False, "login failed")
            return None
    try:
        r = client.get(path)
        html = r.data.decode("utf-8", errors="replace")
        if r.status_code == 500:
            record(name, False, f"500 error")
            print("    TRACEBACK/ERROR:", html[:1500])
            return None
        ok = r.status_code == 200 and marker in html
        record(name, ok, f"status={r.status_code}, marker missing" if not ok else "")
        return r
    except Exception as e:
        record(name, False, str(e))
        traceback.print_exc()
        return None


def test_post(client, name, path, data, expect_redirect=True, role=None, follow=False):
    if role:
        client.get("/logout", follow_redirects=True)
        if not login(client, role):
            record(name, False, "login failed")
            return None
    try:
        r = client.post(path, data=data, follow_redirects=follow)
        html = r.data.decode("utf-8", errors="replace") if r.data else ""
        if r.status_code == 500:
            record(name, False, "500 error")
            print("    TRACEBACK/ERROR:", html[:1500])
            return None
        if expect_redirect and r.status_code not in (302, 303):
            record(name, False, f"expected redirect, got {r.status_code}")
            return None
        if not expect_redirect and r.status_code not in (200, 302, 303, 400, 401):
            record(name, False, f"unexpected status {r.status_code}")
            return None
        record(name, True)
        return r
    except Exception as e:
        record(name, False, str(e))
        traceback.print_exc()
        return None


def run_tests():
    app = create_app()
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        with app.test_client() as client:
            print("\n=== AUTH ===")

            # GET login/register
            test_get(client, "GET /login", "/login", "Sign in")
            test_get(client, "GET /register", "/register", "Create customer account")
            test_get(client, "GET /register-manufacturer", "/register-manufacturer", "Register as manufacturer")

            # POST login each role
            for role in ("customer", "manufacturer", "admin"):
                client.get("/logout", follow_redirects=True)
                r = client.post("/login", data={"email": USERS[role], "password": PASSWORD}, follow_redirects=True)
                ok = r.status_code == 200 and "Invalid email" not in r.data.decode()
                record(f"POST /login ({role})", ok, f"status={r.status_code}")

            # POST bad login
            client.get("/logout", follow_redirects=True)
            r = client.post("/login", data={"email": "bad@test.com", "password": "wrong"}, follow_redirects=True)
            record("POST /login (invalid creds)", r.status_code == 401 and "Invalid email" in r.data.decode())

            # POST register customer (unique email)
            client.get("/logout", follow_redirects=True)
            import uuid
            new_email = f"e2e.customer.{uuid.uuid4().hex[:8]}@test.com"
            r = client.post("/register", data={
                "full_name": "E2E Customer",
                "email": new_email,
                "phone": "555-9999",
                "password": PASSWORD,
            }, follow_redirects=True)
            uid = get_user_id(new_email)
            record("POST /register (customer)", r.status_code == 200 and uid is not None, "user not in DB" if not uid else "")

            # POST register manufacturer
            new_mfg_email = f"e2e.mfg.{uuid.uuid4().hex[:8]}@test.com"
            r = client.post("/register-manufacturer", data={
                "full_name": "E2E Manufacturer",
                "business_name": "E2E Fab Co",
                "email": new_mfg_email,
                "phone": "555-8888",
                "password": PASSWORD,
            }, follow_redirects=True)
            uid_m = get_user_id(new_mfg_email)
            record("POST /register-manufacturer", r.status_code == 200 and uid_m is not None)

            print("\n=== CUSTOMER ===")
            cust_uid = get_user_id(USERS["customer"])
            cp_id = get_customer_profile_id(cust_uid)

            test_get(client, "GET /customer/dashboard", "/customer/dashboard", "Customer Dashboard", "customer")
            test_get(client, "GET /customer/upload", "/customer/upload", "Upload Design", "customer")
            test_get(client, "GET /customer/orders", "/customer/orders", "My Orders", "customer")
            test_get(client, "GET /customer/profile", "/customer/profile", "Profile", "customer")
            r = client.get("/customer/saved-designs")
            record("GET /customer/saved-designs", r.status_code == 200 and "Saved Designs" in r.data.decode())

            # Order detail - get first order for customer
            order_row = db.session.execute(
                db.text("""
                    SELECT o.order_id FROM orders o
                    JOIN manufacturing_requests r ON r.request_id = o.request_id
                    WHERE r.customer_profile_id = :cp LIMIT 1
                """),
                {"cp": cp_id},
            ).first()
            if order_row:
                oid = order_row[0]
                test_get(client, f"GET /customer/orders/{oid}", f"/customer/orders/{oid}", f"Order #{oid}", "customer")
            else:
                record("GET /customer/orders/<id>", False, "no orders in seed data")

            # POST profile
            client.get("/logout", follow_redirects=True)
            login(client, "customer")
            test_post(client, "POST /customer/profile", "/customer/profile", {
                "full_name": "Sarah Chen Updated",
                "phone": "555-0101",
                "company_name": "Acme Industries",
                "address": "1200 Industrial Parkway, Detroit, MI 48201",
            }, role="customer")
            row = db.session.execute(
                db.text("SELECT full_name FROM users WHERE user_id=:u"), {"u": cust_uid}
            ).first()
            record("POST /customer/profile (DB check)", row and row[0] == "Sarah Chen Updated")

            # Saved Designs behavior: draft upload should appear with Continue button
            client.get("/logout", follow_redirects=True)
            login(client, "customer")
            draft_name = "saved_design_draft.stl"
            draft_r = client.post("/customer/upload", data={
                "file": (io.BytesIO(b"solid draft\nendsolid draft\n"), draft_name),
            }, content_type="multipart/form-data", follow_redirects=False)
            draft_request_id = None
            if draft_r.status_code in (302, 303):
                m = re.search(r"/customer/upload/(\d+)/configure", draft_r.headers.get("Location", ""))
                if m:
                    draft_request_id = int(m.group(1))
            record("POST /customer/upload (draft save)", draft_request_id is not None)
            saved = client.get("/customer/saved-designs")
            saved_html = saved.data.decode()
            record("GET /customer/saved-designs (draft file visible)", saved.status_code == 200 and draft_name in saved_html and "Continue" in saved_html)

            # Upload flow
            client.get("/logout", follow_redirects=True)
            login(client, "customer")
            stl_path = app.root_path.replace("app", "").replace("\\app", "") + "/../test.stl"
            import os
            stl_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "test.stl"))
            if not os.path.exists(stl_path):
                stl_content = b"solid test\nendsolid test\n"
            else:
                with open(stl_path, "rb") as f:
                    stl_content = f.read()

            r = client.post("/customer/upload", data={
                "file": (io.BytesIO(stl_content), "e2e_test_part.stl"),
            }, content_type="multipart/form-data", follow_redirects=False)
            if r.status_code not in (302, 303):
                record("POST /customer/upload", False, f"status={r.status_code}")
            else:
                loc = r.headers.get("Location", "")
                m = re.search(r"/customer/upload/(\d+)/configure", loc)
                if not m:
                    record("POST /customer/upload", False, f"bad redirect: {loc}")
                else:
                    request_id = int(m.group(1))
                    record("POST /customer/upload", True)

                    # GET configure
                    r = client.get(f"/customer/upload/{request_id}/configure")
                    record(f"GET /customer/upload/{request_id}/configure", r.status_code == 200 and "Configure" in r.data.decode())

                    # Get process/material IDs
                    proc = db.session.execute(db.text("SELECT process_id FROM manufacturing_processes LIMIT 1")).first()
                    mat = db.session.execute(
                        db.text("SELECT material_id FROM materials WHERE process_id=:p LIMIT 1"),
                        {"p": proc[0]},
                    ).first()

                    r = client.post(f"/customer/upload/{request_id}/configure", data={
                        "process_id": str(proc[0]),
                        "material_id": str(mat[0]),
                        "quantity": "5",
                        "surface_finish": "Standard",
                        "notes": "E2E test order",
                    }, follow_redirects=False)
                    record(f"POST /customer/upload/{request_id}/configure",
                           r.status_code in (302, 303) and "matches" in r.headers.get("Location", ""))

                    r = client.get(f"/customer/upload/{request_id}/matches")
                    html = r.data.decode()
                    record(f"GET /customer/upload/{request_id}/matches", r.status_code == 200 and "Choose" in html)

                    # Find a match form or skip POST if no matches
                    match = db.session.execute(
                        db.text("""
                            SELECT mp.manufacturer_profile_id, mc.machine_id
                            FROM machines mc
                            JOIN manufacturer_profiles mp ON mp.manufacturer_profile_id = mc.manufacturer_profile_id
                            JOIN machine_capabilities cap ON cap.machine_id = mc.machine_id
                            WHERE mc.process_id = :pid AND cap.material_id = :mid AND mc.is_active = TRUE
                            LIMIT 1
                        """),
                        {"pid": proc[0], "mid": mat[0]},
                    ).first()

                    if match:
                        r = client.post(f"/customer/upload/{request_id}/matches", data={
                            "manufacturer_profile_id": str(match[0]),
                            "machine_id": str(match[1]),
                        }, follow_redirects=False)
                        loc = r.headers.get("Location", "")
                        order_m = re.search(r"order_id=(\d+)", loc)
                        record(f"POST /customer/upload/{request_id}/matches",
                               r.status_code in (302, 303) and "confirm" in loc)

                        if order_m:
                            new_oid = order_m.group(1)
                            r = client.get(f"/customer/upload/{request_id}/confirm?order_id={new_oid}")
                            record(f"GET /customer/upload/{request_id}/confirm",
                                   r.status_code == 200 and "Order Placed" in r.data.decode())
                    else:
                        record(f"POST /customer/upload/{request_id}/matches", False, "no matching manufacturer in DB")

            # Saved Designs should link to an existing order-backed file
            order_row_for_saved = db.session.execute(
                db.text("""
                    SELECT o.order_id, uf.filename
                    FROM orders o
                    JOIN manufacturing_requests r ON r.request_id = o.request_id
                    JOIN uploaded_files uf ON uf.file_id = r.file_id
                    WHERE r.customer_profile_id = :cp
                    ORDER BY o.order_id DESC
                    LIMIT 1
                """),
                {"cp": cp_id},
            ).first()
            if order_row_for_saved:
                saved_order_id, saved_filename = order_row_for_saved
                saved_order_page = client.get("/customer/saved-designs")
                saved_order_html = saved_order_page.data.decode()
                record("GET /customer/saved-designs (order-linked file visible)", saved_order_page.status_code == 200 and saved_filename in saved_order_html and "View Order" in saved_order_html and f"/customer/orders/{saved_order_id}" in saved_order_html)
            else:
                record("GET /customer/saved-designs (order-linked file visible)", False, "no order-backed design in seed")

            print("\n=== MANUFACTURER ===")
            mfg_uid = get_user_id(USERS["manufacturer"])
            mp_id = get_manufacturer_profile_id(mfg_uid)

            test_get(client, "GET /manufacturer/dashboard", "/manufacturer/dashboard", "Manufacturer Dashboard", "manufacturer")
            test_get(client, "GET /manufacturer/profile", "/manufacturer/profile", "Profile", "manufacturer")
            test_get(client, "GET /manufacturer/machines", "/manufacturer/machines", "Machines", "manufacturer")
            test_get(client, "GET /manufacturer/available-requests", "/manufacturer/available-requests", "Available Requests", "manufacturer")
            test_get(client, "GET /manufacturer/active-orders", "/manufacturer/active-orders", "Active Orders", "manufacturer")
            test_get(client, "GET /manufacturer/completed-orders", "/manufacturer/completed-orders", "Completed Orders", "manufacturer")

            # POST profile
            client.get("/logout", follow_redirects=True)
            login(client, "manufacturer")
            test_post(client, "POST /manufacturer/profile", "/manufacturer/profile", {
                "full_name": "James Morrison Updated",
                "phone": "555-0201",
                "business_name": "Precision CNC Works",
                "address": "500 Factory Road, Cleveland, OH 44114",
            })
            row = db.session.execute(db.text("SELECT full_name FROM users WHERE user_id=:u"), {"u": mfg_uid}).first()
            record("POST /manufacturer/profile (DB check)", row and row[0] == "James Morrison Updated")

            # Machine add
            proc = db.session.execute(db.text("SELECT process_id FROM manufacturing_processes LIMIT 1")).first()
            mat = db.session.execute(
                db.text("SELECT material_id FROM materials WHERE process_id=:p LIMIT 1"), {"p": proc[0]}
            ).first()

            client.get("/logout", follow_redirects=True)
            login(client, "manufacturer")
            test_get(client, "GET /manufacturer/machines/new", "/manufacturer/machines/new", "Add Machine", "manufacturer")

            r = client.post("/manufacturer/machines/new", data={
                "machine_name": "E2E Test Mill",
                "process_id": str(proc[0]),
                "max_dimensions": "100x100x100 mm",
                "cap_material_id": [str(mat[0])],
                "cap_max_quantity": ["500"],
            }, follow_redirects=False)
            record("POST /manufacturer/machines/new", r.status_code in (302, 303))

            new_machine = db.session.execute(
                db.text("SELECT machine_id FROM machines WHERE machine_name='E2E Test Mill' AND manufacturer_profile_id=:mp"),
                {"mp": mp_id},
            ).first()
            record("POST /manufacturer/machines/new (DB check)", new_machine is not None)

            if new_machine:
                mid = new_machine[0]
                test_get(client, f"GET /manufacturer/machines/{mid}/edit", f"/manufacturer/machines/{mid}/edit", "Edit Machine", "manufacturer")

                r = client.post(f"/manufacturer/machines/{mid}/edit", data={
                    "machine_name": "E2E Test Mill Updated",
                    "process_id": str(proc[0]),
                    "max_dimensions": "200x200x200 mm",
                    "is_active": "true",
                }, follow_redirects=False)
                record(f"POST /manufacturer/machines/{mid}/edit", r.status_code in (302, 303))

                row = db.session.execute(db.text("SELECT machine_name FROM machines WHERE machine_id=:m"), {"m": mid}).first()
                record(f"POST /manufacturer/machines/{mid}/edit (DB check)", row and row[0] == "E2E Test Mill Updated")

                # Add capability
                mat2 = db.session.execute(
                    db.text("SELECT material_id FROM materials WHERE process_id=:p AND material_id != :m LIMIT 1"),
                    {"p": proc[0], "m": mat[0]},
                ).first()
                if mat2:
                    r = client.post(f"/manufacturer/machines/{mid}/capabilities/add", data={
                        "material_id": str(mat2[0]),
                        "max_quantity": "100",
                    }, follow_redirects=False)
                    record(f"POST /manufacturer/machines/{mid}/capabilities/add", r.status_code in (302, 303))

                # Delete machine (cleanup)
                r = client.post(f"/manufacturer/machines/{mid}/delete", follow_redirects=False)
                record(f"POST /manufacturer/machines/{mid}/delete", r.status_code in (302, 303))
                gone = db.session.execute(db.text("SELECT 1 FROM machines WHERE machine_id=:m"), {"m": mid}).first()
                record(f"POST /manufacturer/machines/{mid}/delete (DB check)", gone is None)

            # Accept/reject available request
            avail = db.session.execute(
                db.text("""
                    SELECT order_id FROM orders
                    WHERE manufacturer_profile_id=:mp AND status='Request Submitted' LIMIT 1
                """),
                {"mp": mp_id},
            ).first()

            if avail:
                accept_oid = avail[0]
                client.get("/logout", follow_redirects=True)
                login(client, "manufacturer")
                r = client.post(f"/manufacturer/available-requests/{accept_oid}/accept", follow_redirects=False)
                record(f"POST /manufacturer/available-requests/{accept_oid}/accept", r.status_code in (302, 303))
                st = db.session.execute(db.text("SELECT status FROM orders WHERE order_id=:o"), {"o": accept_oid}).first()
                record(f"POST accept (DB check)", st and st[0] == "Accepted")
            else:
                record("POST /manufacturer/available-requests/accept", False, "no Request Submitted order for James")

            # Reject - need another available request; create one or find from another manufacturer flow
            # Use David's order that's Accepted - can't reject. Need Request Submitted on James.
            # If we accepted above, create a new order for reject test via DB or skip
            reject_avail = db.session.execute(
                db.text("""
                    SELECT o.order_id FROM orders o
                    JOIN manufacturing_requests r ON r.request_id = o.request_id
                    WHERE o.manufacturer_profile_id=:mp AND o.status='Request Submitted' LIMIT 1
                """),
                {"mp": mp_id},
            ).first()
            if not reject_avail:
                # Insert a rejectable order
                req = db.session.execute(
                    db.text("SELECT request_id FROM manufacturing_requests WHERE status='submitted' LIMIT 1")
                ).first()
                mach = db.session.execute(
                    db.text("SELECT machine_id FROM machines WHERE manufacturer_profile_id=:mp LIMIT 1"),
                    {"mp": mp_id},
                ).first()
                if req and mach:
                    ins = db.session.execute(
                        db.text("""
                            INSERT INTO orders (request_id, manufacturer_profile_id, machine_id, status)
                            VALUES (:rid, :mp, :mid, 'Request Submitted') RETURNING order_id
                        """),
                        {"rid": req[0], "mp": mp_id, "mid": mach[0]},
                    ).first()
                    db.session.commit()
                    reject_avail = ins

            if reject_avail:
                reject_oid = reject_avail[0]
                client.get("/logout", follow_redirects=True)
                login(client, "manufacturer")
                r = client.get(f"/manufacturer/available-requests/{reject_oid}/reject")
                record(f"GET /manufacturer/available-requests/{reject_oid}/reject",
                       r.status_code == 200 and "Reject Request" in r.data.decode())

                r = client.post(f"/manufacturer/available-requests/{reject_oid}/reject", data={
                    "reason": "E2E reject test",
                }, follow_redirects=False)
                record(f"POST /manufacturer/available-requests/{reject_oid}/reject", r.status_code in (302, 303))
                st = db.session.execute(db.text("SELECT status FROM orders WHERE order_id=:o"), {"o": reject_oid}).first()
                record(f"POST reject (DB check)", st and st[0] == "Cancelled")

            # Advance order
            active = db.session.execute(
                db.text("""
                    SELECT order_id, status FROM orders
                    WHERE manufacturer_profile_id=:mp AND status IN ('Accepted','Manufacturing','Quality Check')
                    ORDER BY order_id LIMIT 1
                """),
                {"mp": mp_id},
            ).first()

            if active:
                adv_oid, adv_status = active[0], active[1]
                client.get("/logout", follow_redirects=True)
                login(client, "manufacturer")
                r = client.get(f"/manufacturer/active-orders/{adv_oid}/advance")
                record(f"GET /manufacturer/active-orders/{adv_oid}/advance",
                       r.status_code == 200 and "Update Order" in r.data.decode())

                next_map = {"Accepted": "Manufacturing", "Manufacturing": "Quality Check", "Quality Check": "Completed"}
                next_st = next_map.get(adv_status)
                form_data = {"remarks": "E2E advance test"}
                if next_st == "Completed":
                    form_data["final_cost"] = "999.99"

                r = client.post(f"/manufacturer/active-orders/{adv_oid}/advance", data=form_data, follow_redirects=False)
                record(f"POST /manufacturer/active-orders/{adv_oid}/advance", r.status_code in (302, 303))
                st = db.session.execute(db.text("SELECT status FROM orders WHERE order_id=:o"), {"o": adv_oid}).first()
                record(f"POST advance (DB check)", st and st[0] == next_st, f"expected {next_st}, got {st[0] if st else None}")
            else:
                record("GET/POST /manufacturer/active-orders/advance", False, "no active order for James")

            print("\n=== ADMIN ===")
            test_get(client, "GET /admin/dashboard", "/admin/dashboard", "Admin Dashboard", "admin")

            # POST logout
            client.get("/logout", follow_redirects=True)
            login(client, "customer")
            r = client.post("/logout", follow_redirects=False)
            record("POST /logout", r.status_code in (302, 303) and "login" in r.headers.get("Location", ""))

            print("\n=== ROOT REDIRECT ===")
            client.get("/logout", follow_redirects=True)
            r = client.get("/", follow_redirects=False)
            html = r.data.decode("utf-8", errors="replace")
            record("GET / (unauthenticated)", r.status_code == 200 and "3D Marketplace" in html)
            login(client, "customer")
            r = client.get("/", follow_redirects=False)
            record("GET / (customer)", r.status_code in (302, 303) and "customer" in r.headers.get("Location", ""))

    # Summary
    print("\n" + "=" * 60)
    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"])
    print(f"TOTAL: {passed} passed, {failed} failed out of {len(results)}")
    print("=" * 60)
    if failed:
        print("\nFAILURES:")
        for r in results:
            if not r["passed"]:
                print(f"  - {r['name']}: {r['detail']}")
    return failed == 0


if __name__ == "__main__":
    ok = run_tests()
    sys.exit(0 if ok else 1)
