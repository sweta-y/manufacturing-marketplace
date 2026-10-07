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


SIDEBAR_ICONS = {
    "dashboard": '<rect x="3" y="3" width="8" height="8" rx="1.5"/><rect x="13" y="3" width="8" height="5" rx="1.5"/><rect x="13" y="10" width="8" height="11" rx="1.5"/><rect x="3" y="13" width="8" height="8" rx="1.5"/>',
    "upload": '<path d="M12 16V4m0 0L7 9m5-5 5 5"/><path d="M20 16.5a4.5 4.5 0 0 0-2-8.5h-1.2A6.5 6.5 0 1 0 4 15"/>',
    "saved": '<path d="M6 3.75h12v17l-6-4-6 4z"/>',
    "orders": '<path d="m12 3 8 4.5v9L12 21l-8-4.5v-9z"/><path d="m4.5 7.7 7.5 4.4 7.5-4.4M12 12.1V21"/>',
    "track": '<path d="M4 19V5m0 14h16"/><path d="m7 15 4-4 3 2 5-6"/><circle cx="19" cy="7" r="1"/>',
    "notifications": '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/>',
    "help": '<circle cx="12" cy="12" r="9"/><path d="M9.6 9a2.5 2.5 0 1 1 4.2 1.8c-1 .9-1.8 1.2-1.8 2.7M12 17h.01"/>',
}


def sidebar_link(href, label, active=False, icon=None):
    active_class = " active" if active else ""
    aria = ' aria-current="page"' if active else ""
    icon_html = f'<svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{SIDEBAR_ICONS[icon]}</svg>' if icon in SIDEBAR_ICONS else ""
    return f'<a href="{e(href)}" class="sidebar__link{active_class}"{aria}>{icon_html}{e(label)}</a>'
