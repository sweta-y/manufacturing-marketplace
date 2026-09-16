"""
priority_service.py — Service that wraps priority_queue executable to order requests by urgency.
"""
import os
import subprocess
from datetime import datetime


BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
C_MODULE_DIR = os.path.join(BACKEND_DIR, "c_module")
BIN_NAMES = ["priority_queue.exe", "priority_queue"]


def _find_binary():
    for name in BIN_NAMES:
        path = os.path.join(C_MODULE_DIR, name)
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
        if os.path.exists(path):
            return path
    return None


def _python_fallback_sort(requests, now):
    def _key(req):
        days = req.get("estimated_days")
        if days is None or days < 0:
            days = 100000
        created_at = req.get("created_at")
        if isinstance(created_at, datetime):
            wait_hours = max(0.0, (now - created_at).total_seconds() / 3600.0)
        else:
            wait_hours = 0.0
        qty = req.get("quantity") or 1
        return (float(days) * 1000.0) - (wait_hours * 0.01) - (float(qty) * 0.001)

    return sorted(requests, key=_key)


def order_requests_by_priority(requests):
    """
    Given a list of request dictionaries, return (sorted_list, used_fallback).

    sorted_list: requests sorted by priority using the compiled C binary
                 min-heap priority queue (stdin/stdout protocol).
    used_fallback: True if the Python fallback sort was used instead of the
                   C binary (binary missing, crashed, or returned bad data).
    """
    if not requests or len(requests) <= 1:
        return (requests, False)

    now = datetime.now()
    bin_path = _find_binary()

    if not bin_path:
        return (_python_fallback_sort(requests, now), True)

    try:
        lines = [str(len(requests))]
        req_map = {}
        for r in requests:
            oid = int(r.get("order_id", 0))
            req_map[oid] = r
            days = r.get("estimated_days")
            days_val = int(days) if days is not None and days >= 0 else -1
            created_at = r.get("created_at")
            if isinstance(created_at, datetime):
                wait_hours = max(0.0, (now - created_at).total_seconds() / 3600.0)
            else:
                wait_hours = 0.0
            qty = int(r.get("quantity") or 1)
            lines.append(f"{oid} {days_val} {wait_hours:.4f} {qty}")

        stdin_data = "\n".join(lines) + "\n"

        proc = subprocess.run(
            [bin_path],
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=5,
        )

        if proc.returncode == 0 and proc.stdout:
            ordered_ids = [int(line.strip()) for line in proc.stdout.strip().splitlines() if line.strip()]
            ordered = [req_map[oid] for oid in ordered_ids if oid in req_map]
            if len(ordered) == len(requests):
                return (ordered, False)

    except Exception:
        pass

    return (_python_fallback_sort(requests, now), True)