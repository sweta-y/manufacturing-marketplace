"""Truncate all tables and re-seed demo data for presentations."""

from seed_data import get_connection, seed

TRUNCATE_SQL = """
TRUNCATE TABLE
    order_status_history,
    orders,
    request_requirements,
    manufacturing_requests,
    uploaded_files,
    machine_capabilities,
    machines,
    materials,
    manufacturing_processes,
    manufacturer_profiles,
    customer_profiles,
    users
RESTART IDENTITY CASCADE;
"""


def reset_and_seed(conn):
    cur = conn.cursor()
    cur.execute(TRUNCATE_SQL)
    conn.commit()
    cur.close()
    seed(conn)


def main():
    conn = get_connection()
    try:
        reset_and_seed(conn)
        print("Database reset and seeded successfully.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
