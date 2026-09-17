from flask import current_app
from supabase import create_client


def _get_client():
    url = current_app.config.get("SUPABASE_URL")
    anon_key = current_app.config.get("SUPABASE_ANON_KEY")
    if not url or not anon_key:
        raise RuntimeError("Supabase environment variables are not configured")
    return create_client(url, anon_key)


def _user_data(user):
    user_id = getattr(user, "id", None)
    if not user_id and isinstance(user, dict):
        user_id = user.get("id")
    if not user_id:
        raise RuntimeError("Supabase response did not include a user id")
    return {
        "id": str(user_id),
        "uid": str(user_id),
        "email_confirmed": bool(getattr(user, "email_confirmed_at", None)),
    }


def supabase_sign_up(email, password):
    try:
        # Keep email confirmation enabled in production; it is disabled for this dev/demo setup.
        response = _get_client().auth.sign_up({"email": email, "password": password})
        return True, _user_data(response.user)
    except Exception as exc:
        return False, str(exc)


def supabase_sign_in(email, password):
    try:
        response = _get_client().auth.sign_in_with_password({"email": email, "password": password})
        return True, _user_data(response.user)
    except Exception as exc:
        return False, str(exc)