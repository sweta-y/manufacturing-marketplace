import os
import uuid
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"stl", "step", "stp", "obj"}
MAX_SIZE_MB = 50

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def save_upload(file_storage, user_id, base_dir):
    filename = secure_filename(file_storage.filename)
    if not filename or not allowed_file(filename):
        raise ValueError("Invalid file type. Allowed: STL, STEP, STP, OBJ")
    ext = filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    user_dir = os.path.join(base_dir, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    path = os.path.join(user_dir, unique_name)
    file_storage.save(path)
    size_kb = os.path.getsize(path) // 1024
    if size_kb > MAX_SIZE_MB * 1024:
        os.remove(path)
        raise ValueError(f"File too large. Max {MAX_SIZE_MB}MB")
    return {
        "filename": filename,
        "file_type": ext.upper(),
        "file_size_kb": size_kb,
        "storage_path": path,
    }
