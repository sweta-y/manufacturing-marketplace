from flask import session, url_for
from app.models.user import User
from app.pyui.helpers import (
    e,
    format_date,
    format_datetime,
    format_cost,
    order_status_badge,
)
from app.pyui.layout import portal_page


def status_page(message="", approval_status="pending", rejection_reason=None, current_user=None, **kwargs):
    reason_html = ""
    if approval_status == "rejected" and rejection_reason:
        reason_html = f"<p><strong>Reason:</strong> {e(rejection_reason)}</p>"

    content = f"""<div class="main-content__header">
  <h1 class="main-content__title">Account Status</h1>
</div>

<div class="card">
  <div class="card__body" style="padding:var(--space-8);">
    <p style="font-size:var(--font-size-h4);margin-bottom:var(--space-4);">{e(message)}</p>
    {reason_html}
    <p class="text-muted">You will be able to access the manufacturer portal once your registration is approved.</p>
  </div>
</div>"""

    return portal_page(
        portal="manufacturer",
        page_title="Account Status",
        active_nav="status",
        content=content,
        current_user=current_user,
        title="Account Status | 3D Marketplace",
    )


def dashboard_page(stats=None, current_user=None, **kwargs):
    if current_user is None and "user_id" in session:
        current_user = User.query.get(session["user_id"])
    user_name = e(current_user.full_name) if current_user and current_user.full_name else ""
    stats = stats or {}
    machines_cnt = e(stats.get("machines", 0))
    available_cnt = e(stats.get("available", 0))
    active_cnt = e(stats.get("active", 0))

    available_url = url_for("manufacturer.available_requests")
    machines_url = url_for("manufacturer.machines")

    content = f"""<div class="main-content__header">
  <h1 class="main-content__title">Manufacturer Dashboard</h1>
  <p class="main-content__subtitle">Welcome back, {user_name}.</p>
</div>

<div class="grid-3">
  <div class="card">
    <div class="card__body" style="text-align:center;padding:var(--space-8) var(--space-6);">
      <div style="font-size:var(--font-size-h3);font-weight:var(--font-weight-bold);">{machines_cnt}</div>
      <div class="text-muted text-sm">Active Machines</div>
    </div>
  </div>
  <div class="card">
    <div class="card__body" style="text-align:center;padding:var(--space-8) var(--space-6);">
      <div style="font-size:var(--font-size-h3);font-weight:var(--font-weight-bold);">{available_cnt}</div>
      <div class="text-muted text-sm">Available Requests</div>
    </div>
  </div>
  <div class="card">
    <div class="card__body" style="text-align:center;padding:var(--space-8) var(--space-6);">
      <div style="font-size:var(--font-size-h3);font-weight:var(--font-weight-bold);">{active_cnt}</div>
      <div class="text-muted text-sm">Active Orders</div>
    </div>
  </div>
</div>

<div style="display:flex;flex-wrap:wrap;gap:var(--space-3);margin-top:var(--space-6);">
  <a class="btn btn-primary" href="{available_url}">View Requests</a>
  <a class="btn btn-secondary" href="{machines_url}">Manage Machines</a>
</div>"""

    return portal_page(
        portal="manufacturer",
        page_title="Dashboard",
        active_nav="dashboard",
        content=content,
        current_user=current_user,
        title="Dashboard | 3D Marketplace",
    )


def profile_page(profile=None, current_user=None, **kwargs):
    profile = profile or {}
    raw_status = profile.get("approval_status") if hasattr(profile, "get") else getattr(profile, "approval_status", "pending")
    status_str = (raw_status or "pending").lower()
    if status_str == "approved":
        badge_cls = "badge-success"
    elif status_str == "rejected":
        badge_cls = "badge-danger"
    else:
        badge_cls = "badge-pending"

    status_display = e(status_str.capitalize())
    email_val = e(profile.get("email", "") if hasattr(profile, "get") else getattr(profile, "email", ""))
    full_name_val = e(profile.get("full_name", "") if hasattr(profile, "get") else getattr(profile, "full_name", ""))
    phone_val = e(profile.get("phone", "") if hasattr(profile, "get") else getattr(profile, "phone", ""))
    business_name_val = e(profile.get("business_name", "") if hasattr(profile, "get") else getattr(profile, "business_name", ""))
    address_val = e(profile.get("address", "") if hasattr(profile, "get") else getattr(profile, "address", ""))
    profile_action = url_for("manufacturer.profile")

    content = f"""<div class="main-content__header">
  <h1 class="main-content__title">Profile</h1>
  <p class="main-content__subtitle">Manage your account and business details.</p>
</div>

<div class="card" style="max-width:600px;">
  <div class="card__header">
    <span class="card__title">Account Details</span>
    <span class="badge {badge_cls}">
      {status_display}
    </span>
  </div>
  <form method="POST" action="{profile_action}">
    <div class="card__body">
      <div class="form-group">
        <label class="form-label" for="email">Email</label>
        <input class="form-input" type="email" id="email" value="{email_val}" disabled />
      </div>
      <div class="form-group">
        <label class="form-label" for="full_name">Full Name</label>
        <input class="form-input" type="text" id="full_name" name="full_name" value="{full_name_val}" />
      </div>
      <div class="form-group">
        <label class="form-label" for="phone">Phone</label>
        <input class="form-input" type="tel" id="phone" name="phone" value="{phone_val}" />
      </div>
      <div class="form-group">
        <label class="form-label" for="business_name">Business Name</label>
        <input class="form-input" type="text" id="business_name" name="business_name" value="{business_name_val}" />
      </div>
      <div class="form-group">
        <label class="form-label" for="address">Address</label>
        <textarea class="form-textarea" id="address" name="address">{address_val}</textarea>
      </div>
    </div>
    <div class="card__footer">
      <button class="btn btn-primary" type="submit">Save Changes</button>
    </div>
  </form>
</div>"""

    return portal_page(
        portal="manufacturer",
        page_title="Profile",
        active_nav="profile",
        content=content,
        current_user=current_user,
        title="Profile | 3D Marketplace",
    )


def machines_page(machines=None, current_user=None, **kwargs):
    new_machine_url = url_for("manufacturer.machine_new")

    if machines:
        rows_html = []
        for m in machines:
            m_id = m.get("machine_id") if hasattr(m, "get") else getattr(m, "machine_id", "")
            m_name = e(m.get("machine_name") if hasattr(m, "get") else getattr(m, "machine_name", ""))
            p_name = e(m.get("process_name") if hasattr(m, "get") else getattr(m, "process_name", "—") or "—")
            dims = e(m.get("max_dimensions") if hasattr(m, "get") else getattr(m, "max_dimensions", "—") or "—")
            
            caps = m.get("capabilities", []) if hasattr(m, "get") else getattr(m, "capabilities", [])
            if caps:
                caps_html = "".join([
                    f'<span class="badge badge-neutral" style="margin-right:4px;">{e(c.get("material_name") if hasattr(c, "get") else getattr(c, "material_name", "—") or "—")}</span>'
                    for c in caps
                ])
            else:
                caps_html = '<span class="text-muted text-sm">None</span>'

            is_active = m.get("is_active") if hasattr(m, "get") else getattr(m, "is_active", True)
            if is_active:
                status_badge = '<span class="badge badge-success">Active</span>'
            else:
                status_badge = '<span class="badge badge-neutral">Inactive</span>'

            edit_url = url_for("manufacturer.machine_edit", machine_id=m_id)
            del_action = url_for("manufacturer.machine_delete", machine_id=m_id)

            rows_html.append(
                f"""          <tr>
            <td>{m_name}</td>
            <td>{p_name}</td>
            <td>{dims}</td>
            <td>
              {caps_html}
            </td>
            <td>
              {status_badge}
            </td>
            <td style="white-space:nowrap;">
              <a class="btn btn-ghost btn-sm" href="{edit_url}">Edit</a>
              <form method="POST" action="{del_action}" style="display:inline;">
                <button class="btn btn-danger btn-sm" type="submit">Delete</button>
              </form>
            </td>
          </tr>"""
            )
        tbody_content = "\n".join(rows_html)
        table_or_empty = f"""  <div class="table-wrapper">
    <table class="table" aria-label="My machines">
      <thead>
        <tr>
          <th scope="col">Machine</th>
          <th scope="col">Process</th>
          <th scope="col">Max Dimensions</th>
          <th scope="col">Capabilities</th>
          <th scope="col">Status</th>
          <th scope="col">Actions</th>
        </tr>
      </thead>
      <tbody>
{tbody_content}
      </tbody>
    </table>
  </div>"""
    else:
        table_or_empty = '  <p class="text-muted text-sm">You haven\'t added any machines yet.</p>'

    content = f"""<div class="main-content__header" style="display:flex;align-items:flex-start;justify-content:space-between;gap:var(--space-4);flex-wrap:wrap;">
  <div>
    <h1 class="main-content__title">Machines</h1>
    <p class="main-content__subtitle">Manage the machines you manufacture with.</p>
  </div>
  <a class="btn btn-primary" href="{new_machine_url}">+ Add Machine</a>
</div>

{table_or_empty}"""

    return portal_page(
        portal="manufacturer",
        page_title="Machines",
        active_nav="machines",
        content=content,
        current_user=current_user,
        title="Machines | 3D Marketplace",
    )


def machine_form_page(page_title="Add Machine", machine=None, processes=None, materials=None, existing_capabilities=None, form=None, current_user=None, **kwargs):
    processes = processes or []
    materials = materials or []
    existing_capabilities = existing_capabilities or []
    form = form or {}

    subtitle_text = "Update machine details and capabilities." if machine else "Add a new machine and its capabilities."
    
    if machine:
        m_id = machine.get("machine_id") if hasattr(machine, "get") else getattr(machine, "machine_id", "")
        form_action = url_for("manufacturer.machine_edit", machine_id=m_id)
    else:
        form_action = url_for("manufacturer.machine_new")

    proc_options = ['<option value="">Select a process</option>']
    selected_proc_str = str(form.get("process_id") or "")
    for p in processes:
        p_id = str(p.get("process_id") if hasattr(p, "get") else getattr(p, "process_id", ""))
        p_name = p.get("name") if hasattr(p, "get") else getattr(p, "name", "")
        sel = " selected" if selected_proc_str == p_id else ""
        proc_options.append(f'            <option value="{e(p_id)}"{sel}>{e(p_name)}</option>')
    proc_options_html = "\n".join(proc_options)

    refresh_btn_html = ""
    if machine:
        refresh_btn_html = """        <div class="form-group">
          <button class="btn btn-ghost btn-sm" type="submit" name="action" value="refresh_materials">Update material list for selected process</button>
        </div>"""

    status_select_html = ""
    if machine:
        is_active_str = str(form.get("is_active", "true")).lower()
        sel_true = "selected" if is_active_str == "true" else ""
        sel_false = "selected" if is_active_str == "false" else ""
        status_select_html = f"""        <div class="form-group">
          <label class="form-label" for="is_active">Status</label>
          <select class="form-select" id="is_active" name="is_active">
            <option value="true" {sel_true}>Active</option>
            <option value="false" {sel_false}>Inactive</option>
          </select>
        </div>"""

    initial_caps_html = ""
    if not machine:
        mat_options_plain = []
        for m in materials:
            m_id = str(m.get("material_id") if hasattr(m, "get") else getattr(m, "material_id", ""))
            m_name = m.get("name") if hasattr(m, "get") else getattr(m, "name", "")
            mat_options_plain.append(f'                  <option value="{e(m_id)}">{e(m_name)}</option>')
        mat_options_str = "\n".join(mat_options_plain)

        rows = []
        for i in range(3):
            rows.append(
                f"""            <div style="display:flex;gap:var(--space-2);margin-bottom:var(--space-2);flex-wrap:wrap;">
              <select class="form-select" name="cap_material_id" style="flex:2;min-width:180px;">
                <option value="">Material {i + 1}</option>
{mat_options_str}
              </select>
              <input class="form-input" type="number" name="cap_max_quantity" min="1" value="1000" placeholder="Max qty" style="flex:1;min-width:120px;" />
            </div>"""
            )
        initial_caps_html = f"""        <fieldset class="form-group">
          <legend class="form-label">Initial Capabilities (optional)</legend>
{"\n".join(rows)}
        </fieldset>"""

    existing_caps_card_html = ""
    add_cap_card_html = ""
    if machine:
        if existing_capabilities:
            cap_cards = []
            for c in existing_capabilities:
                c_id = c.get("capability_id") if hasattr(c, "get") else getattr(c, "capability_id", "")
                c_mat = e(c.get("material_name") if hasattr(c, "get") else getattr(c, "material_name", "Material") or "Material")
                c_max = e(c.get("max_quantity") if hasattr(c, "get") else getattr(c, "max_quantity", "") or "")
                del_cap_url = url_for("manufacturer.delete_capability", capability_id=c_id)
                cap_cards.append(
                    f"""          <div class="card card--flat">
            <div class="card__body" style="display:flex;align-items:center;justify-content:space-between;padding:var(--space-2) var(--space-3);">
              <span>{c_mat} <span class="text-muted text-sm">(max qty: {c_max})</span></span>
              <form method="POST" action="{del_cap_url}">
                <button class="btn btn-ghost btn-sm" type="submit">Remove</button>
              </form>
            </div>
          </div>"""
                )
            caps_inner_html = "\n".join(cap_cards)
        else:
            caps_inner_html = '        <p class="text-muted text-sm">No capabilities added yet.</p>'

        existing_caps_card_html = f"""  <div class="card" style="max-width:700px;margin-bottom:var(--space-6);">
    <div class="card__header"><span class="card__title">Existing Capabilities</span></div>
    <div class="card__body" style="display:flex;flex-direction:column;gap:var(--space-2);">
{caps_inner_html}
    </div>
  </div>"""

        add_cap_mat_options = ['<option value="">Select a material</option>']
        for m in materials:
            m_id = str(m.get("material_id") if hasattr(m, "get") else getattr(m, "material_id", ""))
            m_name = m.get("name") if hasattr(m, "get") else getattr(m, "name", "")
            add_cap_mat_options.append(f'              <option value="{e(m_id)}">{e(m_name)}</option>')
        add_cap_mat_options_str = "\n".join(add_cap_mat_options)

        m_id = machine.get("machine_id") if hasattr(machine, "get") else getattr(machine, "machine_id", "")
        add_cap_action = url_for("manufacturer.add_capability", machine_id=m_id)
        add_cap_card_html = f"""  <div class="card" style="max-width:700px;">
    <div class="card__header"><span class="card__title">Add Capability</span></div>
    <form method="POST" action="{add_cap_action}">
      <div class="card__body" style="display:flex;gap:var(--space-2);flex-wrap:wrap;align-items:flex-end;">
        <div class="form-group" style="flex:2;min-width:180px;margin-bottom:0;">
          <label class="form-label" for="material_id">Material</label>
          <select class="form-select" id="material_id" name="material_id" required>
{add_cap_mat_options_str}
          </select>
        </div>
        <div class="form-group" style="flex:1;min-width:120px;margin-bottom:0;">
          <label class="form-label" for="max_quantity">Max Qty</label>
          <input class="form-input" type="number" id="max_quantity" name="max_quantity" min="1" value="1000" />
        </div>
        <button class="btn btn-secondary btn-sm" type="submit">+ Add</button>
      </div>
    </form>
  </div>"""

    machines_url = url_for("manufacturer.machines")
    m_name_val = e(form.get("machine_name", ""))
    m_dims_val = e(form.get("max_dimensions", ""))

    content = f"""<div class="main-content__header">
  <h1 class="main-content__title">{e(page_title)}</h1>
  <p class="main-content__subtitle">
    {subtitle_text}
  </p>
</div>

<div class="card" style="max-width:700px;margin-bottom:var(--space-6);">
  <div class="card__header"><span class="card__title">Machine Details</span></div>
  <form method="POST" action="{form_action}">
    <div class="card__body" style="display:flex;flex-direction:column;gap:var(--space-4);">
      <div class="form-group">
        <label class="form-label" for="machine_name">Machine Name</label>
        <input class="form-input" type="text" id="machine_name" name="machine_name" required value="{m_name_val}" />
      </div>

      <div class="form-group">
        <label class="form-label" for="process_id">Process</label>
        <select class="form-select" id="process_id" name="process_id">
{proc_options_html}
        </select>
      </div>

{refresh_btn_html}

      <div class="form-group">
        <label class="form-label" for="max_dimensions">Max Dimensions</label>
        <input class="form-input" type="text" id="max_dimensions" name="max_dimensions" value="{m_dims_val}" placeholder="e.g. 400 x 400 x 300 mm" />
      </div>

{status_select_html}

{initial_caps_html}
    </div>
    <div class="card__footer" style="display:flex;gap:var(--space-3);">
      <button class="btn btn-primary" type="submit">Save Machine</button>
      <a class="btn btn-ghost" href="{machines_url}">Cancel</a>
    </div>
  </form>
</div>

{existing_caps_card_html}

{add_cap_card_html}"""

    return portal_page(
        portal="manufacturer",
        page_title=page_title,
        active_nav="machines",
        content=content,
        current_user=current_user,
        title=f"{page_title} | 3D Marketplace",
    )


def available_requests_page(requests=None, used_fallback=False, current_user=None, **kwargs):
    fallback_banner = ""
    if used_fallback:
        fallback_banner = """<div class="alert alert-warning" role="alert" style="margin-bottom:var(--space-4);">
  <strong>⚠ Fallback Mode:</strong> Priority queue binary not available — using Python fallback sort. Compile <code>priority_queue.c</code> for optimal performance.
</div>"""

    if requests:
        rows_html = []
        for idx, r in enumerate(requests, start=1):
            order_id = r.get("order_id") if hasattr(r, "get") else getattr(r, "order_id", "")
            p_name = e(r.get("process_name") if hasattr(r, "get") else getattr(r, "process_name", "—") or "—")
            m_name = e(r.get("material_name") if hasattr(r, "get") else getattr(r, "material_name", "—") or "—")
            qty = e(r.get("quantity") if hasattr(r, "get") else getattr(r, "quantity", "—") or "—")
            sf = e(r.get("surface_finish") if hasattr(r, "get") else getattr(r, "surface_finish", "—") or "—")
            notes = e(r.get("notes") if hasattr(r, "get") else getattr(r, "notes", "—") or "—")
            fn = e(r.get("filename") if hasattr(r, "get") else getattr(r, "filename", "None") or "None")
            date_str = e(format_date(r.get("created_at") if hasattr(r, "get") else getattr(r, "created_at", "")))
            accept_url = url_for("manufacturer.accept_order", order_id=order_id)
            reject_url = url_for("manufacturer.reject_order", order_id=order_id)
            rows_html.append(
                f"""          <tr>
            <td><span class="badge badge-info">Priority #{idx}</span></td>
            <td>#{e(order_id)}</td>
            <td>{p_name}</td>
            <td>{m_name}</td>
            <td>{qty}</td>
            <td>{sf}</td>
            <td>{notes}</td>
            <td>{fn}</td>
            <td>{date_str}</td>
            <td style="white-space:nowrap;">
              <form method="POST" action="{accept_url}" style="display:inline;">
                <button class="btn btn-primary btn-sm" type="submit">Accept</button>
              </form>
              <a class="btn btn-danger btn-sm" href="{reject_url}">Reject</a>
            </td>
          </tr>"""
            )
        tbody_content = "\n".join(rows_html)
        table_or_empty = f"""  <div class="table-wrapper">
    <table class="table" aria-label="Available requests">
      <thead>
        <tr>
          <th scope="col">Priority</th>
          <th scope="col">Order ID</th>
          <th scope="col">Process</th>
          <th scope="col">Material</th>
          <th scope="col">Qty</th>
          <th scope="col">Surface Finish</th>
          <th scope="col">Notes</th>
          <th scope="col">File</th>
          <th scope="col">Date</th>
          <th scope="col">Actions</th>
        </tr>
      </thead>
      <tbody>
{tbody_content}
      </tbody>
    </table>
  </div>"""
    else:
        table_or_empty = '  <p class="text-muted text-sm">No new requests right now. Check back later.</p>'

    content = f"""{fallback_banner}<div class="main-content__header">
  <h1 class="main-content__title">Available Requests</h1>
  <p class="main-content__subtitle">New manufacturing requests waiting for your response.</p>
</div>

{table_or_empty}"""

    return portal_page(
        portal="manufacturer",
        page_title="Available Requests",
        active_nav="available_requests",
        content=content,
        current_user=current_user,
        title="Available Requests | 3D Marketplace",
    )


def active_orders_page(orders=None, current_user=None, **kwargs):
    if orders:
        rows_html = []
        for o in orders:
            order_id = o.get("order_id") if hasattr(o, "get") else getattr(o, "order_id", "")
            p_name = e(o.get("process_name") if hasattr(o, "get") else getattr(o, "process_name", "—") or "—")
            m_name = e(o.get("material_name") if hasattr(o, "get") else getattr(o, "material_name", "—") or "—")
            qty = e(o.get("quantity") if hasattr(o, "get") else getattr(o, "quantity", "—") or "—")
            badge = order_status_badge(o.get("status") if hasattr(o, "get") else getattr(o, "status", ""))
            updated_str = e(format_datetime(o.get("updated_at") if hasattr(o, "get") else getattr(o, "updated_at", "")))
            next_status = o.get("next_status") if hasattr(o, "get") else getattr(o, "next_status", None)
            if next_status:
                adv_url = url_for("manufacturer.advance_order", order_id=order_id)
                action_cell = f'<a class="btn btn-primary btn-sm" href="{adv_url}">Advance to {e(next_status)}</a>'
            else:
                action_cell = "—"

            rows_html.append(
                f"""          <tr>
            <td>#{e(order_id)}</td>
            <td>{p_name}</td>
            <td>{m_name}</td>
            <td>{qty}</td>
            <td>{badge}</td>
            <td>{updated_str}</td>
            <td>
              {action_cell}
            </td>
          </tr>"""
            )
        tbody_content = "\n".join(rows_html)
        table_or_empty = f"""  <div class="table-wrapper">
    <table class="table" aria-label="Active orders">
      <thead>
        <tr>
          <th scope="col">Order ID</th>
          <th scope="col">Process</th>
          <th scope="col">Material</th>
          <th scope="col">Qty</th>
          <th scope="col">Status</th>
          <th scope="col">Last Updated</th>
          <th scope="col">Actions</th>
        </tr>
      </thead>
      <tbody>
{tbody_content}
      </tbody>
    </table>
  </div>"""
    else:
        table_or_empty = '  <p class="text-muted text-sm">No active orders right now.</p>'

    content = f"""<div class="main-content__header">
  <h1 class="main-content__title">Active Orders</h1>
  <p class="main-content__subtitle">Orders you've accepted, in progress toward completion.</p>
</div>

{table_or_empty}"""

    return portal_page(
        portal="manufacturer",
        page_title="Active Orders",
        active_nav="active_orders",
        content=content,
        current_user=current_user,
        title="Active Orders | 3D Marketplace",
    )


def advance_order_page(order_id, current_status, next_status, customer_price=None,
                       maximum_price=None, current_user=None, **kwargs):
    curr_badge = order_status_badge(current_status)
    next_badge = order_status_badge(next_status)
    form_action = url_for("manufacturer.advance_order", order_id=order_id)
    cancel_url = url_for("manufacturer.active_orders")

    final_cost_html = ""
    if next_status == "Completed":
        if maximum_price is not None:
            limit_text = f"Maximum allowed quote: {format_cost(maximum_price)} (75% of customer price {format_cost(customer_price)})."
            final_cost_html = f"""        <div class="form-group">
          <label class="form-label" for="final_cost">Manufacturer Quote (&#8377;)</label>
          <input class="form-input" type="number" id="final_cost" name="final_cost" placeholder="e.g. 4500" min="0" max="{maximum_price:.2f}" step="0.01" aria-describedby="manufacturer-price-limit" required />
          <p class="form-hint" id="manufacturer-price-limit">{e(limit_text)}</p>
        </div>"""
        else:
            final_cost_html = """        <p class="form-hint">A customer price is unavailable, so a manufacturer quote cannot be submitted.</p>"""

    content = f"""<div class="main-content__header">
  <h1 class="main-content__title">Update Order #{e(order_id)}</h1>
  <p class="main-content__subtitle">
    Current status: {curr_badge}
    → advancing to {next_badge}.
  </p>
</div>

<div class="card" style="max-width:600px;">
  <form method="POST" action="{form_action}">
    <div class="card__body">
{final_cost_html}

      <div class="form-group">
        <label class="form-label" for="remarks">Remarks (optional)</label>
        <textarea class="form-textarea" id="remarks" name="remarks" placeholder="Add a note about this update"></textarea>
      </div>
    </div>
    <div class="card__footer" style="display:flex;gap:var(--space-3);">
      <button class="btn btn-primary" type="submit">Update to {e(next_status)}</button>
      <a class="btn btn-ghost" href="{cancel_url}">Cancel</a>
    </div>
  </form>
</div>"""

    return portal_page(
        portal="manufacturer",
        page_title=f"Update Order #{order_id}",
        active_nav="active_orders",
        content=content,
        current_user=current_user,
        title=f"Update Order #{order_id} | 3D Marketplace",
    )


def completed_orders_page(orders=None, current_user=None, **kwargs):
    if orders:
        rows_html = []
        for o in orders:
            order_id = o.get("order_id") if hasattr(o, "get") else getattr(o, "order_id", "")
            p_name = e(o.get("process_name") if hasattr(o, "get") else getattr(o, "process_name", "—") or "—")
            m_name = e(o.get("material_name") if hasattr(o, "get") else getattr(o, "material_name", "—") or "—")
            qty = e(o.get("quantity") if hasattr(o, "get") else getattr(o, "quantity", "—") or "—")
            final_cost_val = o.get("final_cost") if hasattr(o, "get") else getattr(o, "final_cost", None)
            cost_str = format_cost(final_cost_val)
            updated_str = e(format_datetime(o.get("updated_at") if hasattr(o, "get") else getattr(o, "updated_at", "")))
            rows_html.append(
                f"""          <tr>
            <td>#{e(order_id)}</td>
            <td>{p_name}</td>
            <td>{m_name}</td>
            <td>{qty}</td>
            <td>{cost_str}</td>
            <td>{updated_str}</td>
          </tr>"""
            )
        tbody_content = "\n".join(rows_html)
        table_or_empty = f"""  <div class="table-wrapper">
    <table class="table" aria-label="Completed orders">
      <thead>
        <tr>
          <th scope="col">Order ID</th>
          <th scope="col">Process</th>
          <th scope="col">Material</th>
          <th scope="col">Qty</th>
          <th scope="col">Final Cost</th>
          <th scope="col">Completed On</th>
        </tr>
      </thead>
      <tbody>
{tbody_content}
      </tbody>
    </table>
  </div>"""
    else:
        table_or_empty = '  <p class="text-muted text-sm">You haven\'t completed any orders yet.</p>'

    content = f"""<div class="main-content__header">
  <h1 class="main-content__title">Completed Orders</h1>
  <p class="main-content__subtitle">A record of every order you've finished manufacturing.</p>
</div>

{table_or_empty}"""

    return portal_page(
        portal="manufacturer",
        page_title="Completed Orders",
        active_nav="completed_orders",
        content=content,
        current_user=current_user,
        title="Completed Orders | 3D Marketplace",
    )


def reject_order_page(order_id, current_user=None, **kwargs):
    form_action = url_for("manufacturer.reject_order", order_id=order_id)
    cancel_url = url_for("manufacturer.available_requests")

    content = f"""<div class="main-content__header">
  <h1 class="main-content__title">Reject Request #{e(order_id)}</h1>
  <p class="main-content__subtitle">Optionally provide a reason for rejecting this request.</p>
</div>

<div class="card" style="max-width:600px;">
  <form method="POST" action="{form_action}">
    <div class="card__body">
      <div class="form-group">
        <label class="form-label" for="reason">Reason (optional)</label>
        <textarea class="form-textarea" id="reason" name="reason" placeholder="e.g. Machine unavailable this week"></textarea>
      </div>
    </div>
    <div class="card__footer" style="display:flex;gap:var(--space-3);">
      <button class="btn btn-danger" type="submit">Reject Request</button>
      <a class="btn btn-ghost" href="{cancel_url}">Cancel</a>
    </div>
  </form>
</div>"""

    return portal_page(
        portal="manufacturer",
        page_title="Reject Request",
        active_nav="available_requests",
        content=content,
        current_user=current_user,
        title="Reject Request | 3D Marketplace",
    )
