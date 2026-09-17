"""Migrate uploaded design files to the private Supabase Storage bucket."""

import argparse
import hashlib
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from supabase import create_client


REPO_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_DIR / "backend"
PLACEHOLDER_DIR = BACKEND_DIR / "uploads" / "placeholders"
LOCAL_ROOTS = [
    BACKEND_DIR,
    Path(r"C:\Users\DELL-IN\OneDrive\Desktop\Projects\Capstone project\manufacturing-marketplace\backend"),
    Path(r"C:\Users\DELL-IN\manufacturing-marketplace\backend"),
]
BUCKET_NAME = "design-files"


def storage_object_path(file_id, storage_path, filename):
    if file_id <= 5:
        return f"uploads/customers/{_seed_customer_dir(filename)}/{filename}"
    path = Path(storage_path)
    for root in LOCAL_ROOTS:
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            continue
    path_text = storage_path.replace("\\", "/")
    backend_marker = "/backend/"
    if backend_marker in path_text:
        return path_text.split(backend_marker, 1)[1]
    return storage_path.replace("\\", "/").lstrip("/")


def _seed_customer_dir(filename):
    return {
        "mounting_bracket_v2.step": "sarah",
        "control_panel_face.dxf": "marcus",
        "sensor_housing.stl": "priya",
        "shaft_collar_drawing.pdf": "sarah",
        "display_stand_assembly.stl": "marcus",
    }[filename]


def local_source(file_id, storage_path, filename):
    if file_id <= 5:
        candidate = PLACEHOLDER_DIR / filename
        if candidate.exists():
            return candidate
    path = Path(storage_path)
    candidates = [path] if path.is_absolute() else [root / path for root in LOCAL_ROOTS]
    return next((candidate for candidate in candidates if candidate.exists()), None)


def load_plan():
    conn = psycopg2.connect(os.environ["SUPABASE_DATABASE_URL"])
    try:
        cur = conn.cursor()
        cur.execute("SELECT file_id, storage_path, filename FROM uploaded_files ORDER BY file_id")
        rows = cur.fetchall()
        plan = []
        for file_id, storage_path, filename in rows:
            source = local_source(file_id, storage_path, filename)
            if source is None:
                raise FileNotFoundError(
                    f"No local source for file_id={file_id}, storage_path={storage_path}"
                )
            plan.append((file_id, source, storage_object_path(file_id, storage_path, filename)))
        return plan
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print the upload plan without uploading")
    args = parser.parse_args()
    load_dotenv(REPO_DIR / ".env")
    plan = load_plan()
    client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
    buckets = client.storage.list_buckets()
    bucket_exists = any(getattr(bucket, "name", "") == BUCKET_NAME for bucket in buckets)
    print(f"bucket={BUCKET_NAME} exists={bucket_exists}")
    print(f"total_files={len(plan)} missing_files=0 dry_run={args.dry_run}")
    for index, (file_id, source, object_path) in enumerate(plan, 1):
        print(f"[{index}/{len(plan)}] file_id={file_id} object_path={object_path} source={source} bytes={source.stat().st_size}")
    if args.dry_run:
        return
    if not bucket_exists:
        client.storage.create_bucket(BUCKET_NAME, options={"public": False})
        print(f"created_private_bucket={BUCKET_NAME}")
    bucket = client.storage.from_(BUCKET_NAME)
    uploaded = []
    for index, (file_id, source, object_path) in enumerate(plan, 1):
        bucket.upload(object_path, source.read_bytes(), {"upsert": "true"})
        remote_bytes = bucket.download(object_path)
        local_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        remote_hash = hashlib.sha256(remote_bytes).hexdigest()
        if local_hash != remote_hash:
            raise RuntimeError(
                f"Verification mismatch for file_id={file_id}, object_path={object_path}"
            )
        uploaded.append((file_id, object_path))
        print(f"uploaded_and_verified=[{index}/{len(plan)}] file_id={file_id} object_path={object_path}")

    conn = psycopg2.connect(os.environ["SUPABASE_DATABASE_URL"])
    try:
        cur = conn.cursor()
        for file_id, object_path in uploaded:
            cur.execute(
                "UPDATE uploaded_files SET storage_path = %s WHERE file_id = %s",
                (object_path, file_id),
            )
        conn.commit()
        print(f"database_paths_updated={len(uploaded)}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()