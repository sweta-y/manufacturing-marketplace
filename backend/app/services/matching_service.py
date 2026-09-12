from app.extensions import db

def find_matching_manufacturers(process_id, material_id, quantity):
    sql = db.text("""
        SELECT DISTINCT mp.manufacturer_profile_id, mp.business_name, m.machine_id,
               m.machine_name, m.max_dimensions
        FROM manufacturer_profiles mp
        JOIN machines m ON m.manufacturer_profile_id = mp.manufacturer_profile_id
        JOIN machine_capabilities mc ON mc.machine_id = m.machine_id
        WHERE m.process_id = :process_id
          AND mc.material_id = :material_id
          AND mc.max_quantity >= :quantity
          AND mp.approval_status = 'approved'
          AND m.is_active = TRUE
    """)
    rows = db.session.execute(sql, {
        "process_id": process_id, "material_id": material_id, "quantity": quantity
    }).mappings().all()
    return [dict(r) for r in rows]
