"""
admin_pages.py — Pure Python pyui functions for admin portal pages.
No Jinja2. All user/DB values escaped with e(). HTML structure preserved from templates.
"""
from flask import url_for, session
from app.pyui.helpers import e, format_datetime, format_cost, flash_messages, order_status_badge
from app.pyui.layout import portal_page


from app.models.user import User


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

def dashboard_page(current_user=None, **kwargs):
    if current_user is None and "user_id" in session:
        current_user = User.query.get(session["user_id"])

    name = e(current_user.full_name) if current_user and current_user.full_name else "Admin"
    email = e(current_user.email) if current_user and current_user.email else ""
    approvals_url = url_for("admin.manufacturer_approvals")

    content = f"""<div class="main-content__header">
  <h1 class="main-content__title">Admin Dashboard</h1>
  <p class="main-content__subtitle">Administrative portal.</p>
</div>

<div class="card">
  <div class="card__body">
    <p>Signed in as <strong>{name}</strong> ({email}).</p>
    <div style="margin-top: var(--space-4);">
      <a class="btn btn-primary" href="{approvals_url}">Manufacturer Approvals</a>
    </div>
  </div>
</div>"""

    return portal_page(
        portal="admin",
        page_title="Admin Dashboard",
        active_nav="dashboard",
        content=content,
        current_user=current_user,
        title="Admin Dashboard | 3D Marketplace",
    )


# ─────────────────────────────────────────────────────────────────────────────
# USERS LIST
# ─────────────────────────────────────────────────────────────────────────────

def users_page(users=None, role_filter="all", current_user=None, **kwargs):
    users = users or []
    users_url = url_for("admin.users")

    def _role_badge(role):
        if role == "customer":
            cls = "badge-info"
        elif role == "manufacturer":
            cls = "badge-warning"
        else:
            cls = "badge-danger"
        return f'<span class="badge {cls}">{e(role)}</span>'

    def _status_badge(user):
        role = user.get("role", "")
        status = user.get("status", "")
        if role == "manufacturer":
            if status == "pending":
                return '<span class="badge badge-pending">pending</span>'
            elif status == "rejected":
                return '<span class="badge badge-danger">rejected</span>'
            else:
                return '<span class="badge badge-success">approved</span>'
        else:
            if status == "active":
                return '<span class="badge badge-success">active</span>'
            else:
                return '<span class="badge badge-danger">inactive</span>'

    # Build role filter options
    roles = [("all", "All"), ("customer", "Customer"), ("manufacturer", "Manufacturer"), ("admin", "Admin")]
    options_html = ""
    for val, label in roles:
        sel = ' selected' if role_filter == val else ''
        options_html += f'<option value="{val}"{sel}>{label}</option>'

    filter_form = f"""<div class="card" style="margin-bottom: var(--space-6);">
  <div class="card__body">
    <form method="GET" action="{users_url}" style="display:flex;gap:var(--space-3);flex-wrap:wrap;align-items:center;">
      <label for="role" class="form-label" style="margin:0;">Role</label>
      <select class="form-input" id="role" name="role">
        {options_html}
      </select>
      <button class="btn btn-primary" type="submit">Apply</button>
    </form>
  </div>
</div>"""

    if users:
        rows = ""
        for u in users:
            uid = u.get("user_id", "")
            detail_url = url_for("admin.user_detail", user_id=uid)
            rows += f"""<tr>
          <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{e(u.get("full_name",""))}</td>
          <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{e(u.get("email",""))}</td>
          <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{_role_badge(u.get("role",""))}</td>
          <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{format_datetime(u.get("created_at"))}</td>
          <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{_status_badge(u)}</td>
          <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);text-align:right;"><a href="{detail_url}">Details</a></td>
        </tr>"""
        table = f"""<div class="card">
  <div class="card__body" style="padding:0;">
    <table class="table" style="width:100%;border-collapse:collapse;">
      <thead>
        <tr>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Name</th>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Email</th>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Role</th>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Registered</th>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Status</th>
          <th style="text-align:right;padding:var(--space-3) var(--space-4);">View</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </div>
</div>"""
    else:
        table = '<div class="card"><div class="card__body"><p>No users found for this filter.</p></div></div>'

    content = f"""<div class="main-content__header">
  <h1 class="main-content__title">Users</h1>
  <p class="main-content__subtitle">Platform users and their current status.</p>
</div>

{filter_form}
{table}"""

    return portal_page(
        portal="admin",
        page_title="Users",
        active_nav="users",
        content=content,
        current_user=current_user,
        title="Users Management | 3D Marketplace",
    )


# ─────────────────────────────────────────────────────────────────────────────
# USER DETAIL
# ─────────────────────────────────────────────────────────────────────────────

def user_detail_page(user=None, manufacturer_machines=None, manufacturer_orders=None,
                     customer_orders=None, current_user=None, **kwargs):
    user = user or {}
    manufacturer_machines = manufacturer_machines or []
    manufacturer_orders = manufacturer_orders or []
    customer_orders = customer_orders or []

    users_url = url_for("admin.users")
    role = user.get("role", "")

    # Role badge
    if role == "customer":
        rbcls = "badge-info"
    elif role == "manufacturer":
        rbcls = "badge-warning"
    else:
        rbcls = "badge-danger"

    # Status badge
    if role == "manufacturer":
        appr = user.get("approval_status", "pending")
        if appr == "pending":
            status_badge = '<span class="badge badge-pending">pending</span>'
        elif appr == "rejected":
            status_badge = '<span class="badge badge-danger">rejected</span>'
        else:
            status_badge = '<span class="badge badge-success">approved</span>'
    else:
        is_active = user.get("is_active", True)
        if is_active:
            status_badge = '<span class="badge badge-success">active</span>'
        else:
            status_badge = '<span class="badge badge-danger">inactive</span>'

    # Rejection reason (manufacturer only)
    rejection_html = ""
    if role == "manufacturer" and user.get("rejection_reason"):
        rejection_html = f'<p><strong>Rejection Reason:</strong> {e(user.get("rejection_reason",""))}</p>'

    # Business/company fields
    if role == "manufacturer":
        extra_fields = f"""<p><strong>Business Name:</strong> {e(user.get("business_name","") or "—")}</p>
    <p><strong>Address:</strong> {e(user.get("manufacturer_address","") or "—")}</p>"""
    else:
        extra_fields = f"""<p><strong>Company Name:</strong> {e(user.get("company_name","") or "—")}</p>
    <p><strong>Address:</strong> {e(user.get("customer_address","") or "—")}</p>"""

    # Machines table (manufacturer)
    machines_section = ""
    if role == "manufacturer":
        if manufacturer_machines:
            mrows = ""
            for m in manufacturer_machines:
                mrows += f"""<tr>
            <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{e(m.get("machine_name",""))}</td>
            <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{e(m.get("process_name","") or "—")}</td>
            <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{"Yes" if m.get("is_active") else "No"}</td>
          </tr>"""
            machines_section = f"""<h2 style="margin-bottom:var(--space-3);font-size:var(--font-size-md);">Machines</h2>
<div class="card" style="margin-bottom:var(--space-6);">
  <div class="card__body" style="padding:0;">
    <table class="table" style="width:100%;border-collapse:collapse;">
      <thead>
        <tr>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Machine</th>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Process</th>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Active</th>
        </tr>
      </thead>
      <tbody>
        {mrows}
      </tbody>
    </table>
  </div>
</div>"""
        else:
            machines_section = '<h2 style="margin-bottom:var(--space-3);font-size:var(--font-size-md);">Machines</h2><div class="card" style="margin-bottom:var(--space-6);"><div class="card__body"><p>No machines listed.</p></div></div>'

        # Manufacturer orders
        if manufacturer_orders:
            orows = ""
            for o in manufacturer_orders:
                orows += f"""<tr>
            <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">#{e(str(o.get("order_id","")))}
            </td>
            <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{e(o.get("customer_name",""))}</td>
            <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{e(o.get("status",""))}</td>
            <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{format_datetime(o.get("created_at"))}</td>
          </tr>"""
            machines_section += f"""<h2 style="margin-bottom:var(--space-3);font-size:var(--font-size-md);">Orders</h2>
<div class="card">
  <div class="card__body" style="padding:0;">
    <table class="table" style="width:100%;border-collapse:collapse;">
      <thead>
        <tr>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Order</th>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Customer</th>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Status</th>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Created</th>
        </tr>
      </thead>
      <tbody>
        {orows}
      </tbody>
    </table>
  </div>
</div>"""
        else:
            machines_section += '<h2 style="margin-bottom:var(--space-3);font-size:var(--font-size-md);">Orders</h2><div class="card"><div class="card__body"><p>No orders assigned.</p></div></div>'

    # Customer orders section
    customer_orders_section = ""
    if role == "customer":
        if customer_orders:
            corows = ""
            for o in customer_orders:
                corows += f"""<tr>
            <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">#{e(str(o.get("order_id","")))}
            </td>
            <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{e(o.get("manufacturer_name",""))}</td>
            <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{e(o.get("status",""))}</td>
            <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{format_datetime(o.get("created_at"))}</td>
          </tr>"""
            customer_orders_section = f"""<h2 style="margin-bottom:var(--space-3);font-size:var(--font-size-md);">Orders</h2>
<div class="card">
  <div class="card__body" style="padding:0;">
    <table class="table" style="width:100%;border-collapse:collapse;">
      <thead>
        <tr>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Order</th>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Manufacturer</th>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Status</th>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Created</th>
        </tr>
      </thead>
      <tbody>
        {corows}
      </tbody>
    </table>
  </div>
</div>"""
        else:
            customer_orders_section = '<h2 style="margin-bottom:var(--space-3);font-size:var(--font-size-md);">Orders</h2><div class="card"><div class="card__body"><p>No orders placed.</p></div></div>'

    content = f"""<div class="main-content__header">
  <h1 class="main-content__title">{e(user.get("full_name",""))}</h1>
  <p class="main-content__subtitle">{e(user.get("email",""))}</p>
</div>

<div class="card" style="margin-bottom: var(--space-6);">
  <div class="card__body" style="display:flex;flex-direction:column;gap:var(--space-2);">
    <p><strong>Role:</strong> <span class="badge {rbcls}">{e(role)}</span></p>
    <p><strong>Registration Date:</strong> {format_datetime(user.get("created_at"))}</p>
    <p><strong>Phone:</strong> {e(user.get("phone","") or "—")}</p>
    <p><strong>Status:</strong> {status_badge}</p>
    {rejection_html}
    {extra_fields}
  </div>
</div>

{machines_section}
{customer_orders_section}

<a class="btn btn-secondary" href="{users_url}" style="margin-top:var(--space-6);">Back to Users</a>"""

    return portal_page(
        portal="admin",
        page_title=f"User: {user.get('full_name','')}",
        active_nav="users",
        content=content,
        current_user=current_user,
        title="User Detail | 3D Marketplace",
    )


# ─────────────────────────────────────────────────────────────────────────────
# MACHINES OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────

def machines_page(machines=None, processes=None, manufacturers=None,
                  process_filter="all", manufacturer_filter="all",
                  current_user=None, **kwargs):
    machines = machines or []
    processes = processes or []
    manufacturers = manufacturers or []
    machines_url = url_for("admin.machines")

    process_options = f'<option value="all"{"  selected" if process_filter == "all" else ""}>All</option>'
    for p in processes:
        pid = str(p.get("process_id", ""))
        sel = ' selected' if str(process_filter) == pid else ''
        process_options += f'<option value="{e(pid)}"{sel}>{e(p.get("name",""))}</option>'

    mfr_options = f'<option value="all"{"  selected" if manufacturer_filter == "all" else ""}>All</option>'
    for m in manufacturers:
        mid = str(m.get("manufacturer_profile_id", ""))
        sel = ' selected' if str(manufacturer_filter) == mid else ''
        mfr_options += f'<option value="{e(mid)}"{sel}>{e(m.get("business_name",""))}</option>'

    if machines:
        rows = ""
        for m in machines:
            is_active = m.get("is_active")
            active_badge = '<span class="badge badge-success">active</span>' if is_active else '<span class="badge badge-danger">inactive</span>'
            rows += f"""<tr>
          <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{e(m.get("machine_name",""))}</td>
          <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{e(m.get("manufacturer_name","") or "—")}</td>
          <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{e(m.get("process_name","") or "—")}</td>
          <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{active_badge}</td>
        </tr>"""
        table = f"""<div class="card">
  <div class="card__body" style="padding:0;">
    <table class="table" style="width:100%;border-collapse:collapse;">
      <thead>
        <tr>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Machine</th>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Manufacturer</th>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Process</th>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Active</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </div>
</div>"""
    else:
        table = '<div class="card"><div class="card__body"><p>No machines match these filters.</p></div></div>'

    content = f"""<div class="main-content__header">
  <h1 class="main-content__title">Machines Overview</h1>
  <p class="main-content__subtitle">All machines across all manufacturers.</p>
</div>

<div class="card" style="margin-bottom: var(--space-6);">
  <div class="card__body">
    <form method="GET" action="{machines_url}" style="display:flex;gap:var(--space-3);flex-wrap:wrap;align-items:center;">
      <label for="process_id" class="form-label" style="margin:0;">Process</label>
      <select class="form-input" id="process_id" name="process_id">
        {process_options}
      </select>

      <label for="manufacturer_id" class="form-label" style="margin:0;">Manufacturer</label>
      <select class="form-input" id="manufacturer_id" name="manufacturer_id">
        {mfr_options}
      </select>

      <button class="btn btn-primary" type="submit">Apply</button>
    </form>
  </div>
</div>

{table}"""

    return portal_page(
        portal="admin",
        page_title="Machines Overview",
        active_nav="machines",
        content=content,
        current_user=current_user,
        title="Machines Overview | 3D Marketplace",
    )


# ─────────────────────────────────────────────────────────────────────────────
# ORDERS LIST
# ─────────────────────────────────────────────────────────────────────────────

def orders_page(orders=None, statuses=None, status_filter="all",
                current_user=None, **kwargs):
    orders = orders or []
    statuses = statuses or []
    orders_url = url_for("admin.orders")

    status_options = f'<option value="all"{"  selected" if status_filter == "all" else ""}>All</option>'
    for s in statuses:
        sel = ' selected' if status_filter == s else ''
        status_options += f'<option value="{e(s)}"{sel}>{e(s)}</option>'

    if orders:
        rows = ""
        for o in orders:
            oid = o.get("order_id", "")
            detail_url = url_for("admin.order_detail", order_id=oid)
            mfr_name = e(o.get("manufacturer_business_name","") or o.get("manufacturer_name","") or "—")
            rows += f"""<tr>
          <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">#{e(str(oid))}</td>
          <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{e(o.get("customer_name",""))}</td>
          <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{mfr_name}</td>
          <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{e(o.get("status",""))}</td>
          <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{format_datetime(o.get("created_at"))}</td>
          <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);text-align:right;"><a href="{detail_url}">Details</a></td>
        </tr>"""
        table = f"""<div class="card">
  <div class="card__body" style="padding:0;">
    <table class="table" style="width:100%;border-collapse:collapse;">
      <thead>
        <tr>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Order ID</th>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Customer</th>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Manufacturer</th>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Status</th>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Created</th>
          <th style="text-align:right;padding:var(--space-3) var(--space-4);">View</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </div>
</div>"""
    else:
        table = '<div class="card"><div class="card__body"><p>No orders match this filter.</p></div></div>'

    content = f"""<div class="main-content__header">
  <h1 class="main-content__title">Orders Management</h1>
  <p class="main-content__subtitle">All orders across the platform.</p>
</div>

<div class="card" style="margin-bottom: var(--space-6);">
  <div class="card__body">
    <form method="GET" action="{orders_url}" style="display:flex;gap:var(--space-3);flex-wrap:wrap;align-items:center;">
      <label for="status" class="form-label" style="margin:0;">Status</label>
      <select class="form-input" id="status" name="status">
        {status_options}
      </select>
      <button class="btn btn-primary" type="submit">Apply</button>
    </form>
  </div>
</div>

{table}"""

    return portal_page(
        portal="admin",
        page_title="Orders Management",
        active_nav="orders",
        content=content,
        current_user=current_user,
        title="Orders Management | 3D Marketplace",
    )


# ─────────────────────────────────────────────────────────────────────────────
# ORDER DETAIL
# ─────────────────────────────────────────────────────────────────────────────

def order_detail_page(order=None, history=None, current_user=None, **kwargs):
    order = order or {}
    history = history or []
    orders_url = url_for("admin.orders")
    oid = order.get("order_id", "")

    final_cost = order.get("final_cost")
    cost_str = format_cost(final_cost) if final_cost is not None else "Not yet quoted"

    history_html = ""
    if history:
        items = ""
        for h in history:
            by_name = f' by {e(h.get("changed_by_name",""))}' if h.get("changed_by_name") else ""
            remarks = f'<p class="text-muted text-sm">{e(h.get("remarks",""))}</p>' if h.get("remarks") else ""
            items += f"""<div class="card">
        <div class="card__body" style="padding:var(--space-3) var(--space-4);">
          <strong>{e(h.get("status",""))}</strong>{by_name}
          — <span class="text-muted text-sm">{format_datetime(h.get("changed_at"))}</span>
          {remarks}
        </div>
      </div>"""
        history_html = f'<div style="display:flex;flex-direction:column;gap:var(--space-2);">{items}</div>'
    else:
        history_html = '<p class="text-muted text-sm">No history yet.</p>'

    content = f"""<div class="main-content__header">
  <h1 class="main-content__title">Order #{e(str(oid))}</h1>
  <p class="main-content__subtitle">Full platform order detail.</p>
</div>

<div class="card" style="margin-bottom: var(--space-6);">
  <div class="card__body" style="display:flex;flex-direction:column;gap:var(--space-2);">
    <p><strong>Status:</strong> {order_status_badge(order.get("status",""))}</p>
    <p><strong>Customer:</strong> {e(order.get("customer_name",""))} ({e(order.get("customer_email",""))})</p>
    <p><strong>Manufacturer:</strong> {e(order.get("business_name","") or order.get("manufacturer_contact_name","") or "—")}</p>
    <p><strong>Process:</strong> {e(order.get("process_name","") or "—")}</p>
    <p><strong>Material:</strong> {e(order.get("material_name","") or "—")}</p>
    <p><strong>Quantity:</strong> {e(str(order.get("quantity","") or "—"))}</p>
    <p><strong>Surface Finish:</strong> {e(order.get("surface_finish","") or "—")}</p>
    <p><strong>Notes:</strong> {e(order.get("notes","") or "—")}</p>
    <p><strong>Final Cost:</strong> {cost_str}</p>
    <p><strong>Created:</strong> {format_datetime(order.get("created_at"))}</p>
    <p><strong>Last Updated:</strong> {format_datetime(order.get("updated_at"))}</p>
  </div>
</div>

<h2 style="margin-bottom:var(--space-3);font-size:var(--font-size-md);">Status History</h2>
{history_html}

<a class="btn btn-secondary" href="{orders_url}" style="margin-top:var(--space-6);">Back to Orders</a>"""

    return portal_page(
        portal="admin",
        page_title=f"Order #{oid}",
        active_nav="orders",
        content=content,
        current_user=current_user,
        title=f"Order #{oid} | 3D Marketplace",
    )


# ─────────────────────────────────────────────────────────────────────────────
# REPORTS
# ─────────────────────────────────────────────────────────────────────────────

def reports_page(total_users=None, orders_by_status=None, machine_counts=None,
                 pending_approvals=0, recent_7_days=0, recent_30_days=0,
                 current_user=None, **kwargs):
    total_users = total_users or []
    orders_by_status = orders_by_status or []
    machine_counts = machine_counts or {"total": 0, "active": 0, "inactive": 0}

    total_users_count = sum(r.get("count", 0) for r in total_users)
    total_orders_count = sum(r.get("count", 0) for r in orders_by_status)

    user_rows = ""
    for r in total_users:
        user_rows += f"""<tr>
            <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{e(r.get("role",""))}</td>
            <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);text-align:right;">{r.get("count",0)}</td>
          </tr>"""

    order_rows = ""
    for r in orders_by_status:
        order_rows += f"""<tr>
            <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{e(r.get("status",""))}</td>
            <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);text-align:right;">{r.get("count",0)}</td>
          </tr>"""

    content = f"""<div class="main-content__header">
  <h1 class="main-content__title">Reports &amp; Stats</h1>
  <p class="main-content__subtitle">Platform overview at a glance.</p>
</div>

<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:var(--space-4);margin-bottom:var(--space-6);">
  <div class="card">
    <div class="card__body">
      <div class="text-muted text-sm">Total Users</div>
      <h2 style="margin:var(--space-2) 0 0;">{total_users_count}</h2>
    </div>
  </div>
  <div class="card">
    <div class="card__body">
      <div class="text-muted text-sm">Total Orders</div>
      <h2 style="margin:var(--space-2) 0 0;">{total_orders_count}</h2>
    </div>
  </div>
  <div class="card">
    <div class="card__body">
      <div class="text-muted text-sm">Machines</div>
      <h2 style="margin:var(--space-2) 0 0;">{machine_counts.get("total", 0) or 0}</h2>
    </div>
  </div>
  <div class="card">
    <div class="card__body">
      <div class="text-muted text-sm">Pending Approvals</div>
      <h2 style="margin:var(--space-2) 0 0;">{pending_approvals}</h2>
    </div>
  </div>
  <div class="card">
    <div class="card__body">
      <div class="text-muted text-sm">Orders in 7 days</div>
      <h2 style="margin:var(--space-2) 0 0;">{recent_7_days}</h2>
    </div>
  </div>
  <div class="card">
    <div class="card__body">
      <div class="text-muted text-sm">Orders in 30 days</div>
      <h2 style="margin:var(--space-2) 0 0;">{recent_30_days}</h2>
    </div>
  </div>
</div>

<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:var(--space-6);">
  <div class="card">
    <div class="card__body" style="padding:0;">
      <h2 style="padding:var(--space-4);margin:0;border-bottom:1px solid var(--color-border);">Users by Role</h2>
      <table class="table" style="width:100%;border-collapse:collapse;">
        <thead>
          <tr>
            <th style="text-align:left;padding:var(--space-3) var(--space-4);">Role</th>
            <th style="text-align:right;padding:var(--space-3) var(--space-4);">Count</th>
          </tr>
        </thead>
        <tbody>
          {user_rows}
        </tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <div class="card__body" style="padding:0;">
      <h2 style="padding:var(--space-4);margin:0;border-bottom:1px solid var(--color-border);">Orders by Status</h2>
      <table class="table" style="width:100%;border-collapse:collapse;">
        <thead>
          <tr>
            <th style="text-align:left;padding:var(--space-3) var(--space-4);">Status</th>
            <th style="text-align:right;padding:var(--space-3) var(--space-4);">Count</th>
          </tr>
        </thead>
        <tbody>
          {order_rows}
        </tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <div class="card__body" style="padding:0;">
      <h2 style="padding:var(--space-4);margin:0;border-bottom:1px solid var(--color-border);">Machines</h2>
      <table class="table" style="width:100%;border-collapse:collapse;">
        <thead>
          <tr>
            <th style="text-align:left;padding:var(--space-3) var(--space-4);">State</th>
            <th style="text-align:right;padding:var(--space-3) var(--space-4);">Count</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">Active</td>
            <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);text-align:right;">{machine_counts.get("active", 0) or 0}</td>
          </tr>
          <tr>
            <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">Inactive</td>
            <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);text-align:right;">{machine_counts.get("inactive", 0) or 0}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</div>"""

    return portal_page(
        portal="admin",
        page_title="Reports & Stats",
        active_nav="reports",
        content=content,
        current_user=current_user,
        title="Reports & Stats | 3D Marketplace",
    )


# ─────────────────────────────────────────────────────────────────────────────
# MANUFACTURER APPROVALS
# ─────────────────────────────────────────────────────────────────────────────

def manufacturer_approvals_page(approvals=None, current_user=None, **kwargs):
    approvals = approvals or []

    if approvals:
        rows = ""
        for item in approvals:
            mp_id = item.get("manufacturer_profile_id", "")
            approve_url = url_for("admin.approve_manufacturer", manufacturer_profile_id=mp_id)
            reject_url = url_for("admin.reject_manufacturer", manufacturer_profile_id=mp_id)
            rows += f"""<tr>
          <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{e(item.get("business_name",""))}</td>
          <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">
            {e(item.get("full_name",""))}<br>
            <span class="text-muted text-sm">{e(item.get("email",""))}</span>
          </td>
          <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);">{format_datetime(item.get("created_at"))}</td>
          <td style="padding:var(--space-3) var(--space-4);border-top:1px solid var(--color-border);text-align:right;">
            <div style="display:flex;justify-content:flex-end;gap:var(--space-2);flex-wrap:wrap;">
              <form method="POST" action="{approve_url}">
                <button class="btn btn-primary btn-sm" type="submit">Approve</button>
              </form>
              <form method="POST" action="{reject_url}">
                <input class="form-input" type="text" name="reason" placeholder="Reason (optional)" style="min-width:180px;" />
                <button class="btn btn-secondary btn-sm" type="submit" style="margin-left:var(--space-2);">Reject</button>
              </form>
            </div>
          </td>
        </tr>"""
        table = f"""<div class="card">
  <div class="card__body" style="padding:0;">
    <table class="table" style="width:100%;border-collapse:collapse;">
      <thead>
        <tr>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Business</th>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Contact</th>
          <th style="text-align:left;padding:var(--space-3) var(--space-4);">Registered</th>
          <th style="text-align:right;padding:var(--space-3) var(--space-4);">Actions</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </div>
</div>"""
    else:
        table = '<div class="card"><div class="card__body"><p>No manufacturer registrations are currently pending approval.</p></div></div>'

    content = f"""<div class="main-content__header">
  <h1 class="main-content__title">Manufacturer Approvals</h1>
  <p class="main-content__subtitle">Review pending manufacturer registrations.</p>
</div>

{table}"""

    return portal_page(
        portal="admin",
        page_title="Manufacturer Approvals",
        active_nav="manufacturer_approvals",
        content=content,
        current_user=current_user,
        title="Manufacturer Approvals | 3D Marketplace",
    )
