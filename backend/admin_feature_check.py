from app import create_app
from app.extensions import db

app = create_app()
app.config['WTF_CSRF_ENABLED'] = False

with app.app_context():
    with app.test_client() as client:
        login = client.post('/login', data={'email': 'admin@marketplace.com', 'password': 'Password123!'}, follow_redirects=False)
        print('LOGIN_STATUS', login.status_code)

        pages = [
            '/admin/users',
            '/admin/users?role=manufacturer',
            '/admin/users?role=customer',
            '/admin/machines',
            '/admin/machines?process_id=1',
            '/admin/machines?manufacturer_id=1',
            '/admin/orders',
            '/admin/orders?status=Request%20Submitted',
            '/admin/reports',
        ]

        for path in pages:
            r = client.get(path)
            html = r.get_data(as_text=True)
            print(path, 'STATUS', r.status_code, 'LEN', len(html))

        user_total = db.session.execute(db.text('SELECT COUNT(*) FROM users')).scalar()
        user_roles = db.session.execute(db.text("SELECT role, COUNT(*) FROM users GROUP BY role ORDER BY role")).fetchall()
        machine_total = db.session.execute(db.text('SELECT COUNT(*) FROM machines')).scalar()
        machine_active = db.session.execute(db.text("SELECT is_active, COUNT(*) FROM machines GROUP BY is_active ORDER BY is_active")).fetchall()
        order_total = db.session.execute(db.text('SELECT COUNT(*) FROM orders')).scalar()
        order_status = db.session.execute(db.text('SELECT status, COUNT(*) FROM orders GROUP BY status ORDER BY status')).fetchall()
        pending_approvals = db.session.execute(db.text("SELECT COUNT(*) FROM manufacturer_profiles WHERE approval_status='pending'")).scalar()
        recent_7 = db.session.execute(db.text("SELECT COUNT(*) FROM orders WHERE created_at >= NOW() - INTERVAL '7 days'")).scalar()
        recent_30 = db.session.execute(db.text("SELECT COUNT(*) FROM orders WHERE created_at >= NOW() - INTERVAL '30 days'")).scalar()

        print('USER_TOTAL', user_total)
        print('USER_ROLES', user_roles)
        print('MACHINE_TOTAL', machine_total)
        print('MACHINE_ACTIVE', machine_active)
        print('ORDER_TOTAL', order_total)
        print('ORDER_STATUS', order_status)
        print('PENDING_APPROVALS', pending_approvals)
        print('RECENT_7_DAYS', recent_7)
        print('RECENT_30_DAYS', recent_30)

        sample_user = db.session.execute(db.text("SELECT user_id, full_name, email, role FROM users ORDER BY user_id LIMIT 1")).first()
        sample_machine = db.session.execute(db.text("SELECT machine_id, machine_name FROM machines ORDER BY machine_id LIMIT 1")).first()
        sample_order = db.session.execute(db.text("SELECT order_id, status FROM orders ORDER BY order_id LIMIT 1")).first()
        print('SAMPLE_USER', sample_user)
        print('SAMPLE_MACHINE', sample_machine)
        print('SAMPLE_ORDER', sample_order)
