import os
import subprocess
from app.extensions import db

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
C_MODULE_DIR = os.path.join(BACKEND_DIR, "c_module")
BIN_NAMES = ["match_hash.exe", "match_hash"]


def _find_binary():
    for name in BIN_NAMES:
        path = os.path.join(C_MODULE_DIR, name)
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
        if os.path.exists(path):
            return path
    return None


def find_matching_manufacturers(process_id, material_id, quantity):
    """
    Original SQL JOIN version of capability lookup. Kept as baseline and fallback.
    """
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


def find_matching_manufacturers_via_hash(process_id, material_id, quantity):
    """
    Match customer request (process_id, material_id, quantity) using separate-chaining
    hash table C binary (match_hash / match_hash.exe).

    Returns:
        (matches, used_fallback)
        matches: list of dicts with keys:
                 manufacturer_profile_id, business_name, machine_id, machine_name, max_dimensions
        used_fallback: boolean indicating whether fallback to SQL JOIN was required.
    """
    bin_path = _find_binary()
    if not bin_path:
        return find_matching_manufacturers(process_id, material_id, quantity), True

    try:
        # 1. Fetch raw active machine capabilities without JOIN filtering on target material/process
        caps = db.session.execute(db.text("""
            SELECT m.process_id, mc.material_id, mp.manufacturer_profile_id, m.machine_id, mc.max_quantity
            FROM machines m
            JOIN machine_capabilities mc ON mc.machine_id = m.machine_id
            JOIN manufacturer_profiles mp ON mp.manufacturer_profile_id = m.manufacturer_profile_id
            WHERE mp.approval_status = 'approved' AND m.is_active = TRUE
        """)).mappings().all()

        m_count = len(caps)
        lines = [str(m_count)]
        for c in caps:
            lines.append(f"{c['process_id']} {c['material_id']} {c['manufacturer_profile_id']} {c['machine_id']} {c['max_quantity']}")
        
        # Query line
        lines.append(f"{process_id} {material_id} {quantity}")
        stdin_data = "\n".join(lines) + "\n"

        proc = subprocess.run(
            [bin_path],
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=5,
        )

        if proc.returncode != 0:
            return find_matching_manufacturers(process_id, material_id, quantity), True

        # Parse stdout: "manufacturer_profile_id machine_id" lines
        matched_pairs = []
        for line in proc.stdout.strip().splitlines():
            parts = line.strip().split()
            if len(parts) == 2:
                mp_id, mach_id = int(parts[0]), int(parts[1])
                matched_pairs.append((mp_id, mach_id))

        if not matched_pairs:
            return [], False

        # 2. Fetch business & machine details for the matched pairs
        # Distinct machine IDs to fetch metadata
        mach_ids = list({mach_id for _, mach_id in matched_pairs})
        details = db.session.execute(db.text("""
            SELECT mp.manufacturer_profile_id, mp.business_name, m.machine_id,
                   m.machine_name, m.max_dimensions
            FROM machines m
            JOIN manufacturer_profiles mp ON mp.manufacturer_profile_id = m.manufacturer_profile_id
            WHERE m.machine_id IN :mids
        """).bindparams(db.bindparam("mids", expanding=True)), {"mids": mach_ids}).mappings().all()

        detail_map = {d["machine_id"]: dict(d) for d in details}

        result = []
        seen = set()
        for mp_id, mach_id in matched_pairs:
            if mach_id in detail_map and mach_id not in seen:
                seen.add(mach_id)
                result.append(detail_map[mach_id])

        return result, False

    except Exception:
        return find_matching_manufacturers(process_id, material_id, quantity), True
