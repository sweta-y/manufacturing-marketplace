from flask import session, url_for
from app.models.user import User
from app.pyui.helpers import e, flash_messages, role_badge_class, sidebar_link


def theme_toggle(fixed=False):
    placement = ' style="position:fixed;top:12px;right:12px;z-index:9999;"' if fixed else ""
    return f'<button class="btn btn-secondary btn-sm theme-toggle" type="button" aria-label="Toggle theme"{placement}><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42"/></svg></button>'


def base_layout(title, body_content=None, body=None):
    content = body_content if body_content is not None else (body if body is not None else "")
    tokens_css = url_for("static", filename="css/tokens.css")
    base_css = url_for("static", filename="css/base.css")
    components_css = url_for("static", filename="css/components.css")
    theme_css = url_for("static", filename="css/theme-dark.css")
    has_topbar = 'class="app-shell"' in content
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{e(title)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link rel="stylesheet" href="{tokens_css}" />
  <link rel="stylesheet" href="{base_css}" />
  <link rel="stylesheet" href="{components_css}" />
  <link rel="stylesheet" href="{theme_css}" />
  <script>try{{if(localStorage.getItem("theme")==="dark")document.documentElement.setAttribute("data-theme","dark");}}catch(e){{}}</script>
</head>
<body>
{content if has_topbar else content + theme_toggle(fixed=True)}
  <script>
    document.querySelectorAll(".theme-toggle").forEach(function(button){{
      function updateTheme(theme){{
        document.documentElement.toggleAttribute("data-theme", theme === "dark");
        if(theme === "dark") document.documentElement.setAttribute("data-theme", "dark");
        button.innerHTML = theme === "dark"
          ? '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42"/></svg>'
          : '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.985 12.486a9 9 0 1 1-9.473-9.472c.405-.022.617.46.402.803a6.5 6.5 0 0 0 8.268 8.268c.344-.215.825-.003.803.401z"/></svg>';
      }}
      var currentTheme = document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
      updateTheme(currentTheme);
      button.addEventListener("click", function(){{
        currentTheme = currentTheme === "dark" ? "light" : "dark";
        if(currentTheme === "dark") document.documentElement.setAttribute("data-theme", "dark");
        else document.documentElement.removeAttribute("data-theme");
        try{{localStorage.setItem("theme", currentTheme);}}catch(e){{}}
        updateTheme(currentTheme);
      }});
    }});
  </script>
</body>
</html>
"""


def portal_page(portal, page_title, active_nav, content, current_user=None, title=None):
    if current_user is None and "user_id" in session:
        current_user = User.query.get(session["user_id"])

    if callable(content):
        content = content(current_user)

    if portal == "customer":
        portal_sub = "Customer Portal"
    elif portal == "manufacturer":
        portal_sub = "Manufacturer"
    else:
        portal_sub = "Admin"

    nav_links = []
    if portal == "customer":
        nav_links.append(sidebar_link(url_for("customer.dashboard"), "Dashboard", active_nav == "dashboard"))
        nav_links.append(sidebar_link(url_for("customer.upload_design"), "Upload Design", active_nav == "upload"))
        nav_links.append(sidebar_link(url_for("customer.saved_designs"), "Saved Designs", active_nav == "saved_designs"))
        nav_links.append(sidebar_link(url_for("customer.orders"), "My Orders", active_nav == "orders"))
    elif portal == "manufacturer":
        nav_links.append(sidebar_link(url_for("manufacturer.dashboard"), "Dashboard", active_nav == "dashboard"))
        nav_links.append(sidebar_link(url_for("manufacturer.machines"), "Machines", active_nav == "machines"))
        nav_links.append(sidebar_link(url_for("manufacturer.available_requests"), "Available Requests", active_nav == "available_requests"))
        nav_links.append(sidebar_link(url_for("manufacturer.active_orders"), "Active Orders", active_nav == "active_orders"))
        nav_links.append(sidebar_link(url_for("manufacturer.completed_orders"), "Completed Orders", active_nav == "completed_orders"))
    else:
        nav_links.append(sidebar_link(url_for("admin.dashboard"), "Dashboard", active_nav == "dashboard"))
        nav_links.append(sidebar_link(url_for("admin.users"), "Users", active_nav == "users"))
        nav_links.append(sidebar_link(url_for("admin.machines"), "Machines", active_nav == "machines"))
        nav_links.append(sidebar_link(url_for("admin.orders"), "Orders", active_nav == "orders"))
        nav_links.append(sidebar_link(url_for("admin.reports"), "Reports", active_nav == "reports"))
        nav_links.append(sidebar_link(url_for("admin.manufacturer_approvals"), "Manufacturer Approvals", active_nav == "manufacturer_approvals"))

    account_links = []
    if portal == "manufacturer":
        account_links.append(sidebar_link(url_for("manufacturer.profile"), "Profile", active_nav == "profile"))

    account_section = ""
    if account_links:
        account_section = f"""      <div class="sidebar__section">
        <span class="sidebar__section-label">Account</span>
        {"".join(account_links)}
      </div>"""

    if current_user and current_user.full_name:
        avatar_letter = e(current_user.full_name.strip()[0].upper())
        user_name = e(current_user.full_name)
    else:
        avatar_letter = "?"
        user_name = "User"

    user_role_display = e(portal.capitalize())
    user_container = "a" if portal == "customer" else "div"
    if portal == "customer":
        user_container_attrs = f'class="sidebar__user sidebar__user--profile-link" href="{url_for("customer.profile")}" aria-label="Open customer profile"'
    else:
        user_container_attrs = 'class="sidebar__user"'

    role_badge = ""
    if current_user and current_user.role:
        role_badge = f'<span class="badge {role_badge_class(current_user.role)}">{e(current_user.role)}</span>'

    logout_url = url_for("auth.logout")

    shell_html = f"""<div class="app-shell">
  <aside class="sidebar" id="sidebar" role="navigation" aria-label="{portal.capitalize()} navigation">
    <div class="sidebar__brand">
      <div class="sidebar__brand-icon" aria-hidden="true">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
          <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
          <line x1="12" y1="22.08" x2="12" y2="12"/>
        </svg>
      </div>
      <div>
        <div class="sidebar__brand-name">3D Marketplace</div>
        <div class="sidebar__brand-sub">
          {portal_sub}
        </div>
      </div>
    </div>

    <nav class="sidebar__nav" aria-label="{portal.capitalize()} menu">
      <div class="sidebar__section">
        <span class="sidebar__section-label">Main</span>
        {"".join(nav_links)}
      </div>
{account_section}
    </nav>

    <{user_container} {user_container_attrs}>
      <div class="sidebar__user-avatar" aria-hidden="true">
        {avatar_letter}
      </div>
      <div class="sidebar__user-info">
        <div class="sidebar__user-name">{user_name}</div>
        <div class="sidebar__user-role">{user_role_display}</div>
      </div>
    </{user_container}>
  </aside>

  <header class="topbar" role="banner">
    <div class="topbar__left">
      <span class="topbar__page-title">{e(page_title)}</span>
    </div>
    <div class="topbar__right">
      {role_badge}
      {theme_toggle()}
      <form method="POST" action="{logout_url}" style="display:inline;">
        <button class="btn btn-secondary btn-sm" type="submit">Logout</button>
      </form>
    </div>
  </header>

  <main class="main-content" role="main">
    {flash_messages()}
    {content}
  </main>
</div>
"""
    full_title = title if title is not None else f"{page_title} | 3D Marketplace"
    return base_layout(full_title, shell_html)
