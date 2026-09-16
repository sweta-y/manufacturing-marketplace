"""Seed the manufacturing_marketplace database with realistic demo data."""

import os
from pathlib import Path

import bcrypt
import psycopg2
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

PLACEHOLDER_PASSWORD = "Password123!"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "manufacturing_marketplace"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


def seed(conn):
    password_hash = hash_password(PLACEHOLDER_PASSWORD)
    cur = conn.cursor()

    users = [
        ("admin@marketplace.com", password_hash, "admin", "Jordan Blake", "555-0100"),
        ("sarah.chen@acmeindustries.com", password_hash, "customer", "Sarah Chen", "555-0101"),
        ("marcus.rivera@riveraautomation.com", password_hash, "customer", "Marcus Rivera", "555-0102"),
        ("priya.patel@patelprototypes.com", password_hash, "customer", "Priya Patel", "555-0103"),
        ("james.morrison@precisioncnc.com", password_hash, "manufacturer", "James Morrison", "555-0201"),
        ("elena.vasquez@apexadditive.com", password_hash, "manufacturer", "Elena Vasquez", "555-0202"),
        ("david.okonkwo@lasertechfab.com", password_hash, "manufacturer", "David Okonkwo", "555-0203"),
    ]

    user_ids = {}
    for email, pwd_hash, role, full_name, phone in users:
        cur.execute(
            """
            INSERT INTO users (email, password_hash, role, full_name, phone)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING user_id
            """,
            (email, pwd_hash, role, full_name, phone),
        )
        user_ids[email] = cur.fetchone()[0]

    customers = [
        (user_ids["sarah.chen@acmeindustries.com"], "Acme Industries", "1200 Industrial Parkway, Detroit, MI 48201"),
        (user_ids["marcus.rivera@riveraautomation.com"], "Rivera Automation", "88 Commerce Street, Austin, TX 78701"),
        (user_ids["priya.patel@patelprototypes.com"], "Patel Prototypes", "45 Maker Lane, San Jose, CA 95112"),
    ]

    customer_profile_ids = []
    for user_id, company_name, address in customers:
        cur.execute(
            """
            INSERT INTO customer_profiles (user_id, company_name, address)
            VALUES (%s, %s, %s)
            RETURNING customer_profile_id
            """,
            (user_id, company_name, address),
        )
        customer_profile_ids.append(cur.fetchone()[0])

    manufacturers = [
        (
            user_ids["james.morrison@precisioncnc.com"],
            "Precision CNC Works",
            "500 Factory Road, Cleveland, OH 44114",
        ),
        (
            user_ids["elena.vasquez@apexadditive.com"],
            "Apex Additive Manufacturing",
            "210 Innovation Drive, Boulder, CO 80301",
        ),
        (
            user_ids["david.okonkwo@lasertechfab.com"],
            "LaserTech Fabrication",
            "77 Laser Boulevard, Pittsburgh, PA 15222",
        ),
    ]

    manufacturer_profile_ids = []
    for user_id, business_name, address in manufacturers:
        cur.execute(
            """
            INSERT INTO manufacturer_profiles
                (user_id, business_name, address, approval_status, approved_at)
            VALUES (%s, %s, %s, 'approved', NOW())
            RETURNING manufacturer_profile_id
            """,
            (user_id, business_name, address),
        )
        manufacturer_profile_ids.append(cur.fetchone()[0])

    processes = ["CNC Machining", "3D Printing", "Laser Cutting"]
    process_ids = {}
    for name in processes:
        cur.execute(
            """
            INSERT INTO manufacturing_processes (name)
            VALUES (%s)
            RETURNING process_id
            """,
            (name,),
        )
        process_ids[name] = cur.fetchone()[0]

    materials = [
        ("Aluminum 6061", process_ids["CNC Machining"]),
        ("Stainless Steel 304", process_ids["CNC Machining"]),
        ("PLA Filament", process_ids["3D Printing"]),
        ("Acrylic Sheet", process_ids["Laser Cutting"]),
    ]

    material_ids = {}
    for name, process_id in materials:
        cur.execute(
            """
            INSERT INTO materials (name, process_id)
            VALUES (%s, %s)
            RETURNING material_id
            """,
            (name, process_id),
        )
        material_ids[name] = cur.fetchone()[0]

    machines = [
        (
            manufacturer_profile_ids[0],
            "Haas VF-2 CNC Mill",
            process_ids["CNC Machining"],
            "762x406x508 mm",
        ),
        (
            manufacturer_profile_ids[0],
            "Doosan Lynx 2100 Lathe",
            process_ids["CNC Machining"],
            "210x500 mm",
        ),
        (
            manufacturer_profile_ids[1],
            "Stratasys F370 FDM Printer",
            process_ids["3D Printing"],
            "355x254x355 mm",
        ),
        (
            manufacturer_profile_ids[1],
            "Formlabs Form 3 SLA Printer",
            process_ids["3D Printing"],
            "145x145x185 mm",
        ),
        (
            manufacturer_profile_ids[2],
            "Amada FG-400 Laser Cutter",
            process_ids["Laser Cutting"],
            "4000x2000 mm",
        ),
    ]

    machine_ids = []
    for manufacturer_profile_id, machine_name, process_id, max_dimensions in machines:
        cur.execute(
            """
            INSERT INTO machines
                (manufacturer_profile_id, machine_name, process_id, max_dimensions)
            VALUES (%s, %s, %s, %s)
            RETURNING machine_id
            """,
            (manufacturer_profile_id, machine_name, process_id, max_dimensions),
        )
        machine_ids.append(cur.fetchone()[0])

    capabilities = [
        (machine_ids[0], material_ids["Aluminum 6061"], 500),
        (machine_ids[0], material_ids["Stainless Steel 304"], 300),
        (machine_ids[1], material_ids["Aluminum 6061"], 800),
        (machine_ids[1], material_ids["Stainless Steel 304"], 600),
        (machine_ids[2], material_ids["PLA Filament"], 200),
        (machine_ids[3], material_ids["PLA Filament"], 100),
        (machine_ids[4], material_ids["Acrylic Sheet"], 150),
    ]

    for machine_id, material_id, max_quantity in capabilities:
        cur.execute(
            """
            INSERT INTO machine_capabilities (machine_id, material_id, max_quantity)
            VALUES (%s, %s, %s)
            """,
            (machine_id, material_id, max_quantity),
        )

    uploaded_files = [
        (
            user_ids["sarah.chen@acmeindustries.com"],
            "mounting_bracket_v2.step",
            "step",
            842,
            "uploads/customers/sarah/mounting_bracket_v2.step",
        ),
        (
            user_ids["marcus.rivera@riveraautomation.com"],
            "control_panel_face.dxf",
            "dxf",
            156,
            "uploads/customers/marcus/control_panel_face.dxf",
        ),
        (
            user_ids["priya.patel@patelprototypes.com"],
            "sensor_housing.stl",
            "stl",
            4120,
            "uploads/customers/priya/sensor_housing.stl",
        ),
        (
            user_ids["sarah.chen@acmeindustries.com"],
            "shaft_collar_drawing.pdf",
            "pdf",
            98,
            "uploads/customers/sarah/shaft_collar_drawing.pdf",
        ),
        (
            user_ids["marcus.rivera@riveraautomation.com"],
            "display_stand_assembly.stl",
            "stl",
            2875,
            "uploads/customers/marcus/display_stand_assembly.stl",
        ),
    ]

    file_ids = []
    for user_id, filename, file_type, file_size_kb, storage_path in uploaded_files:
        cur.execute(
            """
            INSERT INTO uploaded_files
                (user_id, filename, file_type, file_size_kb, storage_path)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING file_id
            """,
            (user_id, filename, file_type, file_size_kb, storage_path),
        )
        file_ids.append(cur.fetchone()[0])

    requests = [
        (
            customer_profile_ids[0],
            file_ids[0],
            process_ids["CNC Machining"],
            material_ids["Aluminum 6061"],
            50,
            "Anodized black",
            "Need tight tolerances on mounting holes.",
            1250.00,
            7,
            "submitted",
        ),
        (
            customer_profile_ids[1],
            file_ids[1],
            process_ids["Laser Cutting"],
            material_ids["Acrylic Sheet"],
            25,
            "Polished edge",
            "Clear acrylic, no surface scratches.",
            480.00,
            4,
            "submitted",
        ),
        (
            customer_profile_ids[2],
            file_ids[2],
            process_ids["3D Printing"],
            material_ids["PLA Filament"],
            10,
            "Standard layer height",
            "Functional prototype for fit testing.",
            320.00,
            3,
            "submitted",
        ),
        (
            customer_profile_ids[0],
            file_ids[3],
            process_ids["CNC Machining"],
            material_ids["Stainless Steel 304"],
            100,
            "Passivated",
            "Repeat order from last quarter.",
            2100.00,
            10,
            "submitted",
        ),
        (
            customer_profile_ids[1],
            file_ids[4],
            process_ids["3D Printing"],
            material_ids["PLA Filament"],
            15,
            "Matte finish",
            "Trade show display units.",
            675.00,
            5,
            "submitted",
        ),
    ]

    request_ids = []
    for row in requests:
        cur.execute(
            """
            INSERT INTO manufacturing_requests (
                customer_profile_id, file_id, process_id, material_id,
                quantity, surface_finish, notes, estimated_cost, estimated_days, status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING request_id
            """,
            row,
        )
        request_ids.append(cur.fetchone()[0])

    orders = [
        (request_ids[0], manufacturer_profile_ids[0], machine_ids[0], "Request Submitted", 1250.00),
        (request_ids[1], manufacturer_profile_ids[2], machine_ids[4], "Accepted", 480.00),
        (request_ids[2], manufacturer_profile_ids[1], machine_ids[2], "Manufacturing", 320.00),
        (request_ids[3], manufacturer_profile_ids[0], machine_ids[1], "Quality Check", 2100.00),
        (request_ids[4], manufacturer_profile_ids[1], machine_ids[3], "Completed", 675.00),
    ]

    for request_id, manufacturer_profile_id, machine_id, status, final_cost in orders:
        cur.execute(
            """
            INSERT INTO orders
                (request_id, manufacturer_profile_id, machine_id, status, final_cost)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (request_id, manufacturer_profile_id, machine_id, status, final_cost),
        )

    conn.commit()
    cur.close()


def main():
    conn = get_connection()
    try:
        seed(conn)
        print("Seed data inserted successfully.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
