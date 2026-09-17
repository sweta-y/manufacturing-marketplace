import uuid
from flask import current_app
from supabase import create_client
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"stl", "step", "stp", "obj"}
MAX_SIZE_MB = 50
BUCKET_NAME = "design-files"

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def _storage_bucket():
    url = current_app.config.get("SUPABASE_URL")
    service_key = current_app.config.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not service_key:
        raise RuntimeError("Supabase Storage credentials are not configured")
    return create_client(url, service_key).storage.from_(BUCKET_NAME)


def save_upload(file_storage, user_id, base_dir=None):
    filename = secure_filename(file_storage.filename)
    if not filename or not allowed_file(filename):
        raise ValueError("Invalid file type. Allowed: STL, STEP, STP, OBJ")
    ext = filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    object_path = f"uploads/{user_id}/{unique_name}"
    data = file_storage.read()
    size_kb = len(data) // 1024
    if size_kb > MAX_SIZE_MB * 1024:
        raise ValueError(f"File too large. Max {MAX_SIZE_MB}MB")
    _storage_bucket().upload(object_path, data, {"upsert": "false"})
    return {
        "filename": filename,
        "file_type": ext.upper(),
        "file_size_kb": size_kb,
        "storage_path": object_path,
    }


def create_signed_url(storage_path, expires_in=600):
    response = _storage_bucket().create_signed_url(storage_path, expires_in)
    if isinstance(response, dict):
        return response.get("signedURL") or response.get("signed_url")
    return getattr(response, "signed_url", None) or getattr(response, "signedURL", None)
