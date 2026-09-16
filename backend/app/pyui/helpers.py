import html
from datetime import datetime
from flask import get_flashed_messages, url_for


def e(value):
    if value is None:
        return ""
    return html.escape(str(value))


def format_date(value):
    if not value:
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return str(value)


def format_datetime(value):
    if not value:
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return str(value)


def format_cost(value):
    if value is None:
        return "—"
    try:
        num = float(value)
    except (TypeError, ValueError):
        return "—"
    return f"₹{num:,.2f}"


def flash_messages():
    messages = get_flashed_messages(with_categories=True)
    if not messages:
        return ""
    rendered = []
    for category, message in messages:
        if category == "error":
            cls = "badge-danger"
        elif category == "success":
            cls = "badge-success"
        else:
            cls = "badge-info"
        rendered.append(
            f'<div class="badge {cls}" style="margin-bottom:var(--space-4);padding:var(--space-3) var(--space-4);display:block;">'
            f'{e(message)}'
            f'</div>'
        )
    return "\n".join(rendered)


def role_badge_class(role):
    if role == "customer":
        return "badge-info"
    elif role == "manufacturer":
        return "badge-warning"
    elif role == "admin":
        return "badge-danger"
    return "badge-neutral"


def order_status_badge(status):
    badge_map = {
        "Request Submitted": "badge-pending",
        "Manufacturer Selected": "badge-pending",
        "Accepted": "badge-info",
        "Manufacturing": "badge-warning",
        "Quality Check": "badge-pending",
        "Completed": "badge-success",
        "Cancelled": "badge-danger",
    }
    cls = badge_map.get(status, "badge-neutral")
    return f'<span class="badge {cls}">{e(status)}</span>'


def sidebar_link(href, label, active=False):
    active_class = " active" if active else ""
    aria = ' aria-current="page"' if active else ""
    return f'<a href="{e(href)}" class="sidebar__link{active_class}"{aria}>{e(label)}</a>'
