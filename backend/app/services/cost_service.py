"""Service to call the C cost estimator and parse results."""
import json
import subprocess
import os
from pathlib import Path


# Fallback estimator data (mirrors the C code logic)
_PROCESSES = {
    1: {"name": "CNC Machining", "setup_cost": 500.0, "setup_time": 2.0, "time_per_unit": 0.5},
    2: {"name": "3D Printing", "setup_cost": 100.0, "setup_time": 0.5, "time_per_unit": 0.75},
    3: {"name": "Laser Cutting", "setup_cost": 200.0, "setup_time": 1.0, "time_per_unit": 0.2},
}

_MATERIALS = {
    1: {"name": "Aluminum 6061", "rate_per_unit": 150.0, "multiplier": 1.0},
    2: {"name": "Stainless Steel 304", "rate_per_unit": 220.0, "multiplier": 1.15},
    3: {"name": "PLA Filament", "rate_per_unit": 40.0, "multiplier": 0.8},
    4: {"name": "Acrylic Sheet", "rate_per_unit": 60.0, "multiplier": 0.9},
}


def get_cost_estimator_path():
    """Return the platform-specific path to the cost estimator binary."""
    backend_dir = Path(__file__).parent.parent.parent
    binary_name = "cost_estimator.exe" if os.name == "nt" else "cost_estimator"
    return backend_dir / "c_module" / binary_name


def _estimate_cost_fallback(process_id, material_id, quantity):
    """Python fallback estimator with same logic as C code."""
    process_id = int(process_id)
    material_id = int(material_id)
    quantity = int(quantity)
    
    if quantity <= 0:
        return {"error": "quantity must be positive", "fallback": True}
    
    if process_id not in _PROCESSES:
        return {"error": f"Unknown process_id {process_id}", "fallback": True}
    
    if material_id not in _MATERIALS:
        return {"error": f"Unknown material_id {material_id}", "fallback": True}
    
    p = _PROCESSES[process_id]
    m = _MATERIALS[material_id]
    
    estimated_cost = p["setup_cost"] + (quantity * m["rate_per_unit"] * m["multiplier"])
    estimated_time_hours = p["setup_time"] + (quantity * p["time_per_unit"])
    
    return {
        "process_id": process_id,
        "process_name": p["name"],
        "material_id": material_id,
        "material_name": m["name"],
        "quantity": quantity,
        "estimated_cost": estimated_cost,
        "estimated_time_hours": estimated_time_hours,
        "error": None,
        "fallback": True,
    }


def estimate_cost(process_id, material_id, quantity):
    """
    Call the platform-specific cost estimator binary with process, material, and quantity.
    Falls back to Python estimator if exe is not available.
    
    Returns: dict with keys {estimated_cost, estimated_time_hours}
             or {error: error_message} if estimator fails or is missing.
    """
    estimator_path = get_cost_estimator_path()
    
    # Check if executable exists
    if not estimator_path.exists():
        # Use Python fallback
        result = _estimate_cost_fallback(process_id, material_id, quantity)
        if result.get("error"):
            return {"error": "Cost estimate unavailable (estimator not compiled yet)", "fallback": True}
        return result
    
    try:
        # Call the executable with command-line arguments
        result = subprocess.run(
            [str(estimator_path), str(process_id), str(material_id), str(quantity)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        
        if result.returncode != 0:
            error_msg = result.stdout.strip() if result.stdout else "Unknown error"
            try:
                error_json = json.loads(error_msg)
                if "error" in error_json:
                    # Fall back to Python estimator
                    return _estimate_cost_fallback(process_id, material_id, quantity)
            except json.JSONDecodeError:
                pass
            # Fall back to Python estimator
            return _estimate_cost_fallback(process_id, material_id, quantity)
        
        # Parse JSON output
        output = result.stdout.strip()
        data = json.loads(output)
        
        if "error" in data:
            # Fall back to Python estimator
            return _estimate_cost_fallback(process_id, material_id, quantity)
        
        return {
            "estimated_cost": data.get("estimated_cost"),
            "estimated_time_hours": data.get("estimated_time_hours"),
            "process_name": data.get("process_name"),
            "material_name": data.get("material_name"),
            "error": None,
            "fallback": False,
        }
    
    except subprocess.TimeoutExpired:
        # Fall back to Python estimator
        return _estimate_cost_fallback(process_id, material_id, quantity)
    except Exception:
        # Fall back to Python estimator
        return _estimate_cost_fallback(process_id, material_id, quantity)

