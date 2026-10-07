from flask import session, url_for
from app.models.user import User
from app.pyui.helpers import e, format_date, format_datetime, format_cost, order_status_badge
from app.pyui.layout import portal_page


def dashboard_page(order_count=0, draft_design_count=0, current_user=None, **kwargs):
    if current_user is None and "user_id" in session:
        current_user = User.query.get(session["user_id"])
    user_name = e(current_user.full_name) if current_user and current_user.full_name else ""
    saved_designs_url = url_for("customer.saved_designs")
    upload_url = url_for("customer.upload_design")
    orders_url = url_for("customer.orders")

    content = f"""<div class="main-content__header">
  <h1 class="main-content__title">Customer Dashboard</h1>
  <p class="main-content__subtitle">Welcome back, {user_name}.</p>
</div>

<div class="grid-3">
  <div class="card">
    <div class="card__body" style="text-align:center;padding:var(--space-8) var(--space-6);">
      <div style="font-size:var(--font-size-h3);font-weight:var(--font-weight-bold);">{e(order_count)}</div>
      <div class="text-muted text-sm">Total Orders</div>
    </div>
  </div>
  <div class="card">
    <div class="card__body" style="text-align:center;padding:var(--space-8) var(--space-6);">
      <div style="font-size:var(--font-size-h3);font-weight:var(--font-weight-bold);">{e(draft_design_count)}</div>
      <div class="text-muted text-sm">Draft Designs</div>
      <a href="{saved_designs_url}" class="text-link" style="margin-top:var(--space-3);display:inline-block;">View saved designs</a>
    </div>
  </div>
</div>

<div style="display:flex;flex-wrap:wrap;gap:var(--space-3);margin-top:var(--space-6);">
  <a class="btn btn-primary" href="{upload_url}">Upload Design</a>
  <a class="btn btn-secondary" href="{saved_designs_url}">Saved Designs</a>
  <a class="btn btn-secondary" href="{orders_url}">View My Orders</a>
</div>"""

    return portal_page(
        portal="customer",
        page_title="Dashboard",
        active_nav="dashboard",
        content=content,
        current_user=current_user,
        title="Dashboard | 3D Marketplace",
    )


def upload_step1_page(current_user=None, step=1, **kwargs):
    upload_action = url_for("customer.upload_design")
    content = f"""<div class="main-content__header">
  <h1 class="main-content__title">Upload Your Design</h1>
  <p class="main-content__subtitle">Step 1 — upload a 3D file to begin.</p>
</div>

<div class="card" style="margin-bottom:var(--space-6);">
  <div class="card__body">
    <div class="step-indicator" role="list" aria-label="Order progress">
      <div class="step step--active" role="listitem"><div class="step__pill">1</div><span class="step__label">Upload</span></div>
      <div class="step" role="listitem"><div class="step__pill">2</div><span class="step__label">Configure</span></div>
      <div class="step" role="listitem"><div class="step__pill">3</div><span class="step__label">Matches</span></div>
      <div class="step" role="listitem"><div class="step__pill">4</div><span class="step__label">Confirm</span></div>
    </div>
  </div>
</div>

<div class="card">
  <div class="card__header"><span class="card__title">Step 1 — Upload Your File</span></div>
  <div class="card__body">
    <form method="POST" action="{upload_action}" enctype="multipart/form-data">
      <div class="form-group">
        <label class="form-label" for="file">3D Design File</label>
        <input class="form-input" type="file" id="file" name="file" accept=".stl,.step,.stp,.obj" required />
        <p class="form-hint">Supports .STL, .STEP, .STP, .OBJ — max 50 MB</p>
      </div>
      <button class="btn btn-primary" type="submit">Upload and Continue</button>
    </form>
  </div>
</div>"""

    return portal_page(
        portal="customer",
        page_title="Upload Design",
        active_nav="upload",
        content=content,
        current_user=current_user,
        title="Upload Design | 3D Marketplace",
    )


def upload_configure_page(request=None, req=None, processes=None, materials=None, all_materials=None, selected_process=None, cost_estimate=None, form=None, current_user=None, step=2, **kwargs):
    req_obj = request if request is not None else req
    processes = processes or []
    materials = materials or []
    form = form or {}

    req_id = req_obj.get("request_id") if isinstance(req_obj, dict) or hasattr(req_obj, "get") else getattr(req_obj, "request_id", "")
    req_filename = req_obj.get("filename") if isinstance(req_obj, dict) or hasattr(req_obj, "get") else getattr(req_obj, "filename", "")

    process_options = []
    selected_proc_str = str(form.get("process_id") or "")
    for p in processes:
        p_id = str(p.get("process_id") if hasattr(p, "get") else getattr(p, "process_id", ""))
        p_name = p.get("name") if hasattr(p, "get") else getattr(p, "name", "")
        sel = " selected" if selected_proc_str == p_id else ""
        process_options.append(f'            <option value="{e(p_id)}"{sel}>{e(p_name)}</option>')
    processes_html = "\n".join(process_options)

    material_options = []
    selected_mat_str = str(form.get("material_id") or "")
    for m in materials:
        m_id = str(m.get("material_id") if hasattr(m, "get") else getattr(m, "material_id", ""))
        m_name = m.get("name") if hasattr(m, "get") else getattr(m, "name", "")
        sel = " selected" if selected_mat_str == m_id else ""
        material_options.append(f'            <option value="{e(m_id)}"{sel}>{e(m_name)}</option>')
    materials_html = "\n".join(material_options)

    cost_estimate_html = ""
    if cost_estimate:
        if isinstance(cost_estimate, dict) and cost_estimate.get("error"):
            err_text = cost_estimate.get("error") if not cost_estimate.get("fallback") else "Cost estimate unavailable"
            inner_cost = f"""              <p class="text-muted text-sm">
                <strong>Cost Estimate:</strong> {e(err_text)}
              </p>"""
        else:
            est_cost = float(cost_estimate.get("estimated_cost", 0)) if isinstance(cost_estimate, dict) else float(getattr(cost_estimate, "estimated_cost", 0))
            est_time = float(cost_estimate.get("estimated_time_hours", 0)) if isinstance(cost_estimate, dict) else float(getattr(cost_estimate, "estimated_time_hours", 0))
            p_name = cost_estimate.get("process_name") if isinstance(cost_estimate, dict) else getattr(cost_estimate, "process_name", None)
            m_name = cost_estimate.get("material_name") if isinstance(cost_estimate, dict) else getattr(cost_estimate, "material_name", None)
            subtitle_html = ""
            if p_name and m_name:
                subtitle_html = f"""              <p class="text-muted text-xs" style="margin-top:var(--space-2);">
                {e(p_name)} • {e(m_name)}
              </p>"""
            inner_cost = f"""              <div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-4);">
                <div>
                  <p class="text-muted text-xs">Estimated Cost</p>
                  <p class="text-lg" style="font-weight:600;">${est_cost:.2f}</p>
                </div>
                <div>
                  <p class="text-muted text-xs">Estimated Time</p>
                  <p class="text-lg" style="font-weight:600;">{est_time:.1f} hours</p>
                </div>
              </div>
{subtitle_html}"""

        cost_estimate_html = f"""      <div class="card" style="background-color:var(--color-light-bg);border-left:4px solid var(--color-accent);">
        <div class="card__body">
{inner_cost}
        </div>
      </div>"""

    finish_radios = []
    current_finish = form.get("surface_finish", "Standard")
    for finish in ["Standard", "Fine", "Ultra Fine"]:
        checked = " checked" if current_finish == finish else ""
        finish_radios.append(
            f"""          <label style="display:inline-flex;align-items:center;gap:var(--space-2);margin-right:var(--space-4);">
            <input type="radio" name="surface_finish" value="{e(finish)}"{checked} />
            {e(finish)}
          </label>"""
        )
    finishes_html = "\n".join(finish_radios)

    form_action = url_for("customer.upload_configure", request_id=req_id)
    qty_val = e(form.get("quantity", 1))
    notes_val = e(form.get("notes", ""))

    content = f"""<div class="main-content__header">
  <h1 class="main-content__title">Configure Your Order</h1>
  <p class="main-content__subtitle">Step 2 — tell us how you want it made.</p>
</div>

<div class="card" style="margin-bottom:var(--space-6);">
  <div class="card__body">
    <div class="step-indicator" role="list" aria-label="Order progress">
      <div class="step step--completed" role="listitem"><div class="step__pill">✓</div><span class="step__label">Upload</span></div>
      <div class="step step--active" role="listitem"><div class="step__pill">2</div><span class="step__label">Configure</span></div>
      <div class="step" role="listitem"><div class="step__pill">3</div><span class="step__label">Matches</span></div>
      <div class="step" role="listitem"><div class="step__pill">4</div><span class="step__label">Confirm</span></div>
    </div>
  </div>
</div>

<div class="card">
  <div class="card__header"><span class="card__title">Step 2 — Configure Your Order</span></div>
  <div class="card__body">
    <p class="text-muted text-sm" style="margin-bottom:var(--space-4);">Uploaded file: <strong>{e(req_filename)}</strong></p>

    <form method="POST" action="{form_action}" style="display:flex;flex-direction:column;gap:var(--space-5);">
      <div class="form-group">
        <label class="form-label" for="process_id">Manufacturing Process</label>
        <select class="form-select" id="process_id" name="process_id">
{processes_html}
        </select>
      </div>

      <div class="form-group">
        <button class="btn btn-ghost btn-sm" type="submit" name="action" value="refresh_materials">Update material list for selected process</button>
      </div>

      <div class="form-group">
        <label class="form-label" for="material_id">Material</label>
        <select class="form-select" id="material_id" name="material_id">
{materials_html}
        </select>
      </div>

      <div class="form-group">
        <label class="form-label" for="quantity">Quantity</label>
        <div style="display:flex;gap:var(--space-2);">
          <input class="form-input" type="number" id="quantity" name="quantity" min="1" max="999" value="{qty_val}" required style="flex:1;" />
          <button class="btn btn-ghost btn-sm" type="submit" name="action" value="recalculate_estimate" style="white-space:nowrap;">Recalculate Cost</button>
        </div>
      </div>

{cost_estimate_html}

      <fieldset class="form-group">
        <legend class="form-label">Surface Finish</legend>
{finishes_html}
      </fieldset>

      <div class="form-group">
        <label class="form-label" for="notes">Notes (optional)</label>
        <textarea class="form-textarea" id="notes" name="notes" rows="3">{notes_val}</textarea>
      </div>

      <button class="btn btn-primary" type="submit">Find Manufacturers</button>
    </form>
  </div>
</div>"""

    return portal_page(
        portal="customer",
        page_title="Configure Order",
        active_nav="upload",
        content=content,
        current_user=current_user,
        title="Configure Order | 3D Marketplace",
    )


def upload_matches_page(request_id, matches, current_user=None, step=3, **kwargs):
    if not matches:
        back_url = url_for("customer.upload_configure", request_id=request_id)
        matches_html = f"""    <p class="text-muted text-sm">No manufacturers currently match this configuration. Try a different process or material.</p>
    <a class="btn btn-secondary" href="{back_url}">Back to Configure</a>"""
    else:
        cards = []
        action_url = url_for("customer.upload_matches", request_id=request_id)
        for m in matches:
            b_name = e(m.get("business_name") if hasattr(m, "get") else getattr(m, "business_name", ""))
            m_name = e(m.get("machine_name") if hasattr(m, "get") else getattr(m, "machine_name", ""))
            max_dims = e(m.get("max_dimensions") if hasattr(m, "get") else getattr(m, "max_dimensions", "—") or "—")
            mp_id = e(m.get("manufacturer_profile_id") if hasattr(m, "get") else getattr(m, "manufacturer_profile_id", ""))
            mach_id = e(m.get("machine_id") if hasattr(m, "get") else getattr(m, "machine_id", ""))
            cards.append(
                f"""      <div class="card">
        <div class="card__body" style="display:flex;justify-content:space-between;align-items:center;gap:var(--space-4);flex-wrap:wrap;">
          <div>
            <strong>{b_name}</strong>
            <p class="text-muted text-sm">{m_name} — max {max_dims}</p>
          </div>
          <form method="POST" action="{action_url}">
            <input type="hidden" name="manufacturer_profile_id" value="{mp_id}" />
            <input type="hidden" name="machine_id" value="{mach_id}" />
            <button class="btn btn-primary btn-sm" type="submit">Select &amp; Place Order</button>
          </form>
        </div>
      </div>"""
            )
        matches_html = "\n".join(cards)

    content = f"""<div class="main-content__header">
  <h1 class="main-content__title">Choose a Manufacturer</h1>
  <p class="main-content__subtitle">Step 3 — select who will make your order.</p>
</div>

<div class="card" style="margin-bottom:var(--space-6);">
  <div class="card__body">
    <div class="step-indicator" role="list" aria-label="Order progress">
      <div class="step step--completed" role="listitem"><div class="step__pill">✓</div><span class="step__label">Upload</span></div>
      <div class="step step--completed" role="listitem"><div class="step__pill">✓</div><span class="step__label">Configure</span></div>
      <div class="step step--active" role="listitem"><div class="step__pill">3</div><span class="step__label">Matches</span></div>
      <div class="step" role="listitem"><div class="step__pill">4</div><span class="step__label">Confirm</span></div>
    </div>
  </div>
</div>

<div class="card">
  <div class="card__header"><span class="card__title">Step 3 — Choose a Manufacturer</span></div>
  <div class="card__body" style="display:flex;flex-direction:column;gap:var(--space-3);">
{matches_html}
  </div>
</div>"""

    return portal_page(
        portal="customer",
        page_title="Choose Manufacturer",
        active_nav="upload",
        content=content,
        current_user=current_user,
        title="Choose Manufacturer | 3D Marketplace",
    )


def upload_confirm_page(order, current_user=None, step=4, **kwargs):
    order_id = e(order.get("order_id") if hasattr(order, "get") else getattr(order, "order_id", ""))
    business_name = e(order.get("business_name") if hasattr(order, "get") else getattr(order, "business_name", ""))
    orders_url = url_for("customer.orders")

    content = f"""<div class="main-content__header">
  <h1 class="main-content__title">Order Placed</h1>
  <p class="main-content__subtitle">Step 4 — confirmation.</p>
</div>

<div class="card" style="margin-bottom:var(--space-6);">
  <div class="card__body">
    <div class="step-indicator" role="list" aria-label="Order progress">
      <div class="step step--completed" role="listitem"><div class="step__pill">✓</div><span class="step__label">Upload</span></div>
      <div class="step step--completed" role="listitem"><div class="step__pill">✓</div><span class="step__label">Configure</span></div>
      <div class="step step--completed" role="listitem"><div class="step__pill">✓</div><span class="step__label">Matches</span></div>
      <div class="step step--active" role="listitem"><div class="step__pill">✓</div><span class="step__label">Confirm</span></div>
    </div>
  </div>
</div>

<div class="card">
  <div class="card__header"><span class="card__title">Order Placed Successfully</span></div>
  <div class="card__body">
    <p>Order #{order_id} placed successfully with <strong>{business_name}</strong>.</p>
    <a class="btn btn-primary" href="{orders_url}" style="margin-top:var(--space-4);">View My Orders</a>
  </div>
</div>"""

    return portal_page(
        portal="customer",
        page_title="Order Placed",
        active_nav="upload",
        content=content,
        current_user=current_user,
        title="Order Placed | 3D Marketplace",
    )


def saved_designs_page(designs, current_user=None, **kwargs):
    if designs:
        rows_html = []
        for d in designs:
            fn = e(d.get("filename") if hasattr(d, "get") else getattr(d, "filename", ""))
            uploaded = e(format_datetime(d.get("uploaded_at") if hasattr(d, "get") else getattr(d, "uploaded_at", "")))
            status = e(d.get("status") if hasattr(d, "get") else getattr(d, "status", ""))
            action_url = d.get("action_url") if hasattr(d, "get") else getattr(d, "action_url", None)
            action_label = e(d.get("action_label") if hasattr(d, "get") else getattr(d, "action_label", ""))
            download_url = d.get("download_url") if hasattr(d, "get") else getattr(d, "download_url", None)
            if action_url:
                action_cell = f'<a class="btn btn-primary btn-sm" href="{e(action_url)}">{action_label}</a>'
            else:
                action_cell = '<span class="text-muted text-sm">No action</span>'
            action_cell += f' <a class="btn btn-secondary btn-sm" href="{e(download_url)}">Download</a>' if download_url else ""
            rows_html.append(
                f"""          <tr>
            <td>{fn}</td>
            <td>{uploaded}</td>
            <td>{status}</td>
            <td>
              {action_cell}
            </td>
          </tr>"""
            )
        tbody_content = "\n".join(rows_html)
        table_or_empty = f"""  <div class="table-wrapper">
    <table class="table" aria-label="Saved designs">
      <thead>
        <tr>
          <th scope="col">Filename</th>
          <th scope="col">Uploaded</th>
          <th scope="col">Status</th>
          <th scope="col">Action</th>
        </tr>
      </thead>
      <tbody>
{tbody_content}
      </tbody>
    </table>
  </div>"""
    else:
        upload_url = url_for("customer.upload_design")
        table_or_empty = f"""  <p class="text-muted text-sm">You don't have any saved design files yet.</p>
  <a class="btn btn-primary" href="{upload_url}" style="margin-top:var(--space-4);">Upload a Design</a>"""

    content = f"""<div class="main-content__header">
  <h1 class="main-content__title">Saved Designs</h1>
  <p class="main-content__subtitle">Review uploaded design files and continue where you left off.</p>
</div>

{table_or_empty}"""

    return portal_page(
        portal="customer",
        page_title="Saved Designs",
        active_nav="saved_designs",
        content=content,
        current_user=current_user,
        title="Saved Designs | 3D Marketplace",
    )


def orders_page(orders, current_user=None, **kwargs):
    if orders:
        rows_html = []
        for o in orders:
            order_id = o.get("order_id") if hasattr(o, "get") else getattr(o, "order_id", "")
            process_name = e(o.get("process_name") if hasattr(o, "get") else getattr(o, "process_name", "—") or "—")
            material_name = e(o.get("material_name") if hasattr(o, "get") else getattr(o, "material_name", "—") or "—")
            quantity = e(o.get("quantity") if hasattr(o, "get") else getattr(o, "quantity", "—") or "—")
            business_name = e(o.get("business_name") if hasattr(o, "get") else getattr(o, "business_name", "—") or "—")
            badge = order_status_badge(o.get("status") if hasattr(o, "get") else getattr(o, "status", ""))
            date_str = e(format_date(o.get("created_at") if hasattr(o, "get") else getattr(o, "created_at", "")))
            detail_url = url_for("customer.order_detail", order_id=order_id)
            rows_html.append(
                f"""          <tr>
            <td>#{e(order_id)}</td>
            <td>{process_name}</td>
            <td>{material_name}</td>
            <td>{quantity}</td>
            <td>{business_name}</td>
            <td>{badge}</td>
            <td>{date_str}</td>
            <td><a href="{detail_url}">View</a></td>
          </tr>"""
            )
        tbody_content = "\n".join(rows_html)
        table_or_empty = f"""  <div class="table-wrapper">
    <table class="table" aria-label="My orders">
      <thead>
        <tr>
          <th scope="col">Order ID</th>
          <th scope="col">Process</th>
          <th scope="col">Material</th>
          <th scope="col">Qty</th>
          <th scope="col">Manufacturer</th>
          <th scope="col">Status</th>
          <th scope="col">Date</th>
          <th scope="col">Details</th>
        </tr>
      </thead>
      <tbody>
{tbody_content}
      </tbody>
    </table>
  </div>"""
    else:
        upload_url = url_for("customer.upload_design")
        table_or_empty = f"""  <p class="text-muted text-sm">You haven't placed any orders yet.</p>
  <a class="btn btn-primary" href="{upload_url}" style="margin-top:var(--space-4);">Upload a Design</a>"""

    content = f"""<div class="main-content__header">
  <h1 class="main-content__title">My Orders</h1>
  <p class="main-content__subtitle">Track the status of every order you've placed.</p>
</div>

{table_or_empty}"""

    return portal_page(
        portal="customer",
        page_title="My Orders",
        active_nav="orders",
        content=content,
        current_user=current_user,
        title="My Orders | 3D Marketplace",
    )


def track_production_page(orders, current_user=None, **kwargs):
    if orders:
        cards = []
        for order in orders:
            order_id = order.get("order_id")
            status = order.get("status") or ""
            status_label = "Awaiting Production" if status in ("Request Submitted", "Manufacturer Selected") else status
            expected = order.get("expected_completion")
            expected_html = f'<p><strong>Expected completion:</strong> {e(format_date(expected))}</p>' if expected else ""
            history = order.get("history") or []
            if history:
                history_html = "".join(
                    f'''<li style="padding:var(--space-2) 0;border-bottom:1px solid var(--color-border);">
                      <strong>{e(event.get("status"))}</strong>
                      <span class="text-muted text-sm">{e(format_datetime(event.get("changed_at")))}</span>
                      {f'<p class="text-muted text-sm">{e(event.get("remarks"))}</p>' if event.get("remarks") else ""}
                    </li>'''
                    for event in history
                )
                timeline = f'<ol aria-label="Order status timeline" style="list-style:none;padding:0;margin:var(--space-3) 0 0;">{history_html}</ol>'
            else:
                timeline = '<p class="text-muted text-sm">No status history recorded yet.</p>'
            cards.append(
                f'''<div class="card" style="margin-bottom:var(--space-4);">
                  <div class="card__header"><span class="card__title">Order #{e(order_id)}</span>{order_status_badge(status_label)}</div>
                  <div class="card__body">
                    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:var(--space-3);">
                      <p><strong>Design / part:</strong> {e(order.get("filename") or "—")}</p>
                      <p><strong>Process:</strong> {e(order.get("process_name") or "—")}</p>
                      <p><strong>Material:</strong> {e(order.get("material_name") or "—")}</p>
                      <p><strong>Quantity:</strong> {e(order.get("quantity") or "—")}</p>
                      <p><strong>Order date:</strong> {e(format_date(order.get("created_at")))}</p>
                      {expected_html}
                    </div>
                    <h2 style="font-size:var(--font-size-md);margin-top:var(--space-4);">Status timeline</h2>
                    {timeline}
                  </div>
                </div>'''
            )
        content_body = "".join(cards)
    else:
        content_body = '''<div class="empty-state">
          <h2 class="empty-state__title">No active production</h2>
          <p class="empty-state__desc">Your active manufacturing orders will appear here.</p>
        </div>'''

    content = f'''<div class="main-content__header">
      <h1 class="main-content__title">Track Production</h1>
      <p class="main-content__subtitle">Follow the latest recorded status of your active orders.</p>
    </div>
    {content_body}'''
    return portal_page(
        portal="customer", page_title="Track Production", active_nav="track_production",
        content=content, current_user=current_user, title="Track Production | 3D Marketplace",
    )


def notifications_page(notifications, current_user=None, **kwargs):
    if notifications:
        items = []
        for notification in notifications:
            read_state = "Read" if notification.get("is_read") else "Unread"
            state_class = "badge-neutral" if notification.get("is_read") else "badge-info"
            items.append(
                f'''<div class="card" style="margin-bottom:var(--space-3);">
                  <div class="card__body" style="display:flex;justify-content:space-between;align-items:flex-start;gap:var(--space-3);">
                    <div><p>{e(notification.get("message"))}</p>
                    <span class="text-muted text-sm">{e(format_datetime(notification.get("created_at")))}</span></div>
                    <span class="badge {state_class}">{read_state}</span>
                  </div>
                </div>'''
            )
        content_body = "".join(items)
    else:
        content_body = '''<div class="empty-state">
          <h2 class="empty-state__title">No notifications yet</h2>
        </div>'''

    content = f'''<div class="main-content__header">
      <h1 class="main-content__title">Notifications</h1>
      <p class="main-content__subtitle">Order and account updates for your marketplace activity.</p>
    </div>
    {content_body}'''
    return portal_page(
        portal="customer", page_title="Notifications", active_nav="notifications",
        content=content, current_user=current_user, title="Notifications | 3D Marketplace",
    )


def help_support_page(current_user=None, **kwargs):
    upload_url = url_for("customer.upload_design")
    saved_url = url_for("customer.saved_designs")
    track_url = url_for("customer.track_production")
    orders_url = url_for("customer.orders")
    content = f'''<div class="main-content__header">
      <h1 class="main-content__title">Help &amp; Support</h1>
      <p class="main-content__subtitle">Quick guidance for using the manufacturing marketplace.</p>
    </div>
    <div class="card"><div class="card__body">
      <h2>How do I upload a design?</h2>
      <p>Choose a 3D design file in STL, STEP, STP, or OBJ format (up to 50 MB), then select a process, material, and quantity.</p>
      <p><a class="text-link" href="{upload_url}">Upload Design</a></p>
      <h2>How does manufacturing work?</h2>
      <p>After configuring a request, review available manufacturer matches and submit an order. The order status is updated as it moves through the marketplace workflow.</p>
      <h2>How can I track an order?</h2>
      <p>Use Track Production for active orders or My Orders to review all orders and their recorded status history.</p>
      <p><a class="text-link" href="{track_url}">Track Production</a> · <a class="text-link" href="{orders_url}">My Orders</a></p>
      <h2>Where are my uploaded designs?</h2>
      <p>Saved Designs lists your uploaded files and whether they are still drafts, submitted, or associated with an order.</p>
      <p><a class="text-link" href="{saved_url}">View Saved Designs</a></p>
      <h2>What do order statuses mean?</h2>
      <p>Supported statuses are Request Submitted, Manufacturer Selected, Accepted, Manufacturing, Quality Check, Completed, and Cancelled. Updates and timestamps appear in the order status history when recorded.</p>
    </div></div>'''
    return portal_page(
        portal="customer", page_title="Help & Support", active_nav="help_support",
        content=content, current_user=current_user, title="Help & Support | 3D Marketplace",
    )


def order_detail_page(order, history, current_user=None, **kwargs):
    order_id = order.get("order_id") if hasattr(order, "get") else getattr(order, "order_id", "")
    status_badge = order_status_badge(order.get("status") if hasattr(order, "get") else getattr(order, "status", ""))
    business_name = e(order.get("business_name") if hasattr(order, "get") else getattr(order, "business_name", "—") or "—")
    process_name = e(order.get("process_name") if hasattr(order, "get") else getattr(order, "process_name", "—") or "—")
    material_name = e(order.get("material_name") if hasattr(order, "get") else getattr(order, "material_name", "—") or "—")
    quantity = e(order.get("quantity") if hasattr(order, "get") else getattr(order, "quantity", "—") or "—")
    surface_finish = e(order.get("surface_finish") if hasattr(order, "get") else getattr(order, "surface_finish", "—") or "—")
    notes = e(order.get("notes") if hasattr(order, "get") else getattr(order, "notes", "—") or "—")
    
    final_cost_val = order.get("final_cost") if hasattr(order, "get") else getattr(order, "final_cost", None)
    if final_cost_val is not None:
        cost_str = format_cost(final_cost_val)
    else:
        cost_str = "Not yet quoted"
    
    created_at_val = order.get("created_at") if hasattr(order, "get") else getattr(order, "created_at", None)
    placed_str = e(format_datetime(created_at_val))

    if history:
        history_cards = []
        for h in history:
            h_status = e(h.get("status") if hasattr(h, "get") else getattr(h, "status", ""))
            changed_at_val = h.get("changed_at") if hasattr(h, "get") else getattr(h, "changed_at", None)
            h_date = e(format_datetime(changed_at_val))
            remarks_val = h.get("remarks") if hasattr(h, "get") else getattr(h, "remarks", None)
            remarks_html = f'<p class="text-muted text-sm">{e(remarks_val)}</p>' if remarks_val else ""
            history_cards.append(
                f"""      <div class="card">
        <div class="card__body" style="padding:var(--space-3) var(--space-4);">
          <strong>{h_status}</strong> —
          <span class="text-muted text-sm">{h_date}</span>
          {remarks_html}
        </div>
      </div>"""
            )
        history_html = f"""  <div style="display:flex;flex-direction:column;gap:var(--space-2);">
{"\n".join(history_cards)}
  </div>"""
    else:
        history_html = '  <p class="text-muted text-sm">No history yet.</p>'

    orders_url = url_for("customer.orders")

    content = f"""<div class="main-content__header">
  <h1 class="main-content__title">Order #{e(order_id)}</h1>
  <p class="main-content__subtitle">Order details and status history.</p>
</div>

<div class="card" style="margin-bottom:var(--space-6);">
  <div class="card__body" style="display:flex;flex-direction:column;gap:var(--space-2);">
    <p><strong>Status:</strong> {status_badge}</p>
    <p><strong>Manufacturer:</strong> {business_name}</p>
    <p><strong>Process:</strong> {process_name}</p>
    <p><strong>Material:</strong> {material_name}</p>
    <p><strong>Quantity:</strong> {quantity}</p>
    <p><strong>Surface Finish:</strong> {surface_finish}</p>
    <p><strong>Notes:</strong> {notes}</p>
    <p><strong>Final Cost:</strong> {cost_str}</p>
    <p><strong>Placed:</strong> {placed_str}</p>
  </div>
</div>

<h2 style="margin-bottom:var(--space-3);font-size:var(--font-size-md);">Status History</h2>
{history_html}

<a class="btn btn-secondary" href="{orders_url}" style="margin-top:var(--space-6);">Back to Orders</a>"""

    return portal_page(
        portal="customer",
        page_title=f"Order #{order_id}",
        active_nav="orders",
        content=content,
        current_user=current_user,
        title=f"Order #{order_id} | 3D Marketplace",
    )


def profile_page(profile=None, current_user=None, **kwargs):
    profile = profile or {}
    email_val = e(profile.get("email", "") if hasattr(profile, "get") else getattr(profile, "email", ""))
    full_name_val = e(profile.get("full_name", "") if hasattr(profile, "get") else getattr(profile, "full_name", ""))
    phone_val = e(profile.get("phone", "") if hasattr(profile, "get") else getattr(profile, "phone", ""))
    company_name_val = e(profile.get("company_name", "") if hasattr(profile, "get") else getattr(profile, "company_name", ""))
    address_val = e(profile.get("address", "") if hasattr(profile, "get") else getattr(profile, "address", ""))
    profile_action = url_for("customer.profile")

    content = f"""<div class="main-content__header">
  <h1 class="main-content__title">Profile</h1>
  <p class="main-content__subtitle">Manage your account details.</p>
</div>

<div class="card" style="max-width:600px;">
  <div class="card__header"><span class="card__title">Account Details</span></div>
  <form method="POST" action="{profile_action}">
    <div class="card__body">
      <div class="form-group">
        <label class="form-label" for="email">Email</label>
        <input class="form-input" type="email" id="email" value="{email_val}" disabled />
        <p class="form-hint">Email cannot be changed.</p>
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
        <label class="form-label" for="company_name">Company Name</label>
        <input class="form-input" type="text" id="company_name" name="company_name" value="{company_name_val}" />
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
        portal="customer",
        page_title="Profile",
        active_nav="profile",
        content=content,
        current_user=current_user,
        title="Profile | 3D Marketplace",
    )
