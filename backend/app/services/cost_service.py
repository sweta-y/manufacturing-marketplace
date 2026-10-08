"""Rule-based INR cost estimator used by the customer configuration flow."""
import json
import os
import subprocess
from pathlib import Path


# Rates are per job, per modeled production hour, or per piece, as indicated.
# The estimator has no part dimensions or weights, so material is priced per
# configured piece and production uses the existing process time-per-piece.
_PROCESSES = {
    1: {"name": "CNC Machining", "setup_cost": 500.0, "setup_time": 2.0, "time_per_unit": 0.5, "hourly_rate": 800.0},
    2: {"name": "3D Printing", "setup_cost": 100.0, "setup_time": 0.5, "time_per_unit": 0.75, "hourly_rate": 250.0},
    3: {"name": "Laser Cutting", "setup_cost": 200.0, "setup_time": 1.0, "time_per_unit": 0.2, "hourly_rate": 500.0},
}

_MATERIALS = {
    1: {"name": "Aluminum 6061", "rate_per_unit": 150.0, "multiplier": 1.0},
    2: {"name": "Stainless Steel 304", "rate_per_unit": 220.0, "multiplier": 1.15},
    3: {"name": "PLA Filament", "rate_per_unit": 40.0, "multiplier": 0.8},
    4: {"name": "Acrylic Sheet", "rate_per_unit": 60.0, "multiplier": 0.9},
}


_FINISH_RATES = {"Standard": 0.0, "Fine": 50.0, "Ultra Fine": 120.0}


def get_cost_estimator_path():
    backend_dir = Path(__file__).parent.parent.parent
    binary_name = "cost_estimator.exe" if os.name == "nt" else "cost_estimator"
    return backend_dir / "c_module" / binary_name


def _calculate_estimate(process_id, material_id, quantity, surface_finish="Standard"):
    """Calculate an INR estimate and its auditable component breakdown."""
    process_id = int(process_id)
    material_id = int(material_id)
    quantity = int(quantity)
    surface_finish = str(surface_finish or "Standard")
    
    if quantity <= 0:
        return {"error": "quantity must be positive", "fallback": True}
    
    if process_id not in _PROCESSES:
        return {"error": f"Unknown process_id {process_id}", "fallback": True}
    
    if material_id not in _MATERIALS:
        return {"error": f"Unknown material_id {material_id}", "fallback": True}
    if surface_finish not in _FINISH_RATES:
        return {"error": "Unknown surface finish", "fallback": True}
    
    p = _PROCESSES[process_id]
    m = _MATERIALS[material_id]
    
    setup_cost = p["setup_cost"]
    material_cost = quantity * m["rate_per_unit"] * m["multiplier"]
    machining_cost = quantity * p["time_per_unit"] * p["hourly_rate"]
    surface_finish_cost = quantity * _FINISH_RATES[surface_finish]
    estimated_cost = setup_cost + material_cost + machining_cost + surface_finish_cost
    estimated_time_hours = p["setup_time"] + (quantity * p["time_per_unit"])
    
    return {
        "process_id": process_id,
        "process_name": p["name"],
        "material_id": material_id,
        "material_name": m["name"],
        "quantity": quantity,
        "estimated_cost": estimated_cost,
        "cost_breakdown": {
            "setup_cost": setup_cost,
            "material_cost": material_cost,
            "machining_cost": machining_cost,
            "surface_finish_cost": surface_finish_cost,
            "estimated_total": estimated_cost,
        },
        "surface_finish": surface_finish,
        "estimated_time_hours": estimated_time_hours,
        "error": None,
        "fallback": False,
    }


def estimate_cost(process_id, material_id, quantity, surface_finish="Standard"):
    """Return the estimate, time, and line items from the single backend formula."""
    estimator_path = get_cost_estimator_path()
    if estimator_path.exists():
        try:
            result = subprocess.run(
                [str(estimator_path), str(process_id), str(material_id), str(quantity), str(surface_finish)],
                capture_output=True, text=True, timeout=5, check=True,
            )
            data = json.loads(result.stdout)
            if not data.get("error") and data.get("cost_breakdown"):
                data["error"] = None
                data["fallback"] = False
                return data
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError, ValueError):
            pass
    return _calculate_estimate(process_id, material_id, quantity, surface_finish)
