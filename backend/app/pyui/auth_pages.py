"""
auth_pages.py — Pure Python pyui functions for auth pages.
No Jinja2. All user/form values escaped with e(). HTML structure preserved from templates.
"""
from flask import url_for
from app.pyui.helpers import e, flash_messages
from app.pyui.layout import base_layout


def _auth_visual(eyebrow, heading, features=None):
    feature_items = ""
    if features:
        feature_items = "".join(
            f"""<span class="auth-page__grid-item">
          <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            {icon}
          </svg>
          <small>{e(label)}</small>
        </span>"""
            for label, icon in features
        )
    else:
        feature_items = "<span></span>" * 12

    return f"""  <div class="auth-page__visual" aria-hidden="true">
    <div class="auth-page__panel">
      <div class="auth-page__brand">
        <div class="landing-brand__mark">
          <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
            <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
            <line x1="12" y1="22.08" x2="12" y2="12"/>
          </svg>
        </div>
        <span>3D Marketplace</span>
      </div>
      <div class="auth-page__spec">
        <span class="eyebrow">{e(eyebrow)}</span>
        <h2>{e(heading)}</h2>
      </div>
      <div class="auth-page__grid" aria-hidden="true">
        {feature_items}
      </div>
    </div>
  </div>"""


def login_page(next_url=None, email="", **kwargs):
    login_url = url_for("auth.login")
    index_url = url_for("index")
    register_url = url_for("auth.register")
    register_mfr_url = url_for("auth.register_manufacturer")

    next_input = f'<input type="hidden" name="next" value="{e(next_url)}" />' if next_url else ""

    features = [
        ("3D Printing", '<path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Z"/><path d="m4.3 7.7 7.7 4.4 7.7-4.4M12 12.1V21"/>'),
        ("CNC Machining", '<circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2M12 4V2M12 22v-2"/>'),
        ("Injection Molding", '<path d="M7 4h10v16H7z"/><path d="M4 8h3M17 8h3M4 16h3M17 16h3M10 8h4v8h-4z"/>'),
        ("Sheet Metal", '<path d="M4 6h16v12H4z"/><path d="m4 6 4 4h12M8 10v8"/>'),
        ("Laser Cutting", '<path d="m13 3-2 7h5l-5 11 2-8H8l5-10Z"/>'),
        ("Metal Casting", '<path d="M5 5h14v14H5z"/><path d="M8 9h8M8 13h5M8 17h8"/>'),
        ("Rapid Prototyping", '<path d="M12 3v5M12 16v5M3 12h5M16 12h5"/><circle cx="12" cy="12" r="4"/>'),
        ("Surface Finishing", '<path d="m4 17 6-6 4 4 6-6"/><path d="m17 5 3 4-4 1M4 21h16"/>'),
        ("Quality Inspection", '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4M8 11l2 2 4-4"/>'),
        ("Verified Suppliers", '<path d="M5 6h14v13H5z"/><path d="M8 6V4h8v2M8 11l2 2 5-5"/>'),
        ("Instant Quotes", '<path d="M12 3v18M16 7.5c-.7-1-2-1.5-4-1.5-2.2 0-4 1.1-4 3s1.8 3 4 3 4 1.1 4 3-1.8 3-4 3c-2 0-3.3-.5-4-1.5"/>'),
        ("Order Tracking", '<circle cx="12" cy="12" r="8"/><path d="M12 7v5l3 2"/>'),
    ]
    visual = _auth_visual("Production network", "Precision manufacturing supply chain.", features)
    body = f"""<div class="auth-page auth-page--login">
{visual}

  <div class="auth-page__form-wrap">
    <div class="auth-card">
      <div class="auth-card__header">
        <div>
          <div class="eyebrow eyebrow--dark">Welcome back</div>
          <h1>Sign in</h1>
        </div>
        <a class="text-link" href="{index_url}">Back to home</a>
      </div>

      {flash_messages()}

      <form method="POST" action="{login_url}" class="auth-form">
        {next_input}

        <div class="form-group">
          <label class="form-label" for="email">Email</label>
          <input class="form-input" type="email" id="email" name="email" required value="{e(email or '')}" />
        </div>

        <div class="form-group">
          <label class="form-label" for="password">Password</label>
          <input class="form-input" type="password" id="password" name="password" required />
        </div>

        <button class="btn btn-primary" type="submit">Login</button>
      </form>

      <div class="auth-card__links">
        <p>New customer? <a href="{register_url}">Create an account</a></p>
        <p>Manufacturer? <a href="{register_mfr_url}">Register as manufacturer</a></p>
      </div>
    </div>
  </div>
</div>"""

    return base_layout(title="Login | 3D Marketplace", body_content=body)


def register_page(form=None, **kwargs):
    form = form or {}
    register_url = url_for("auth.register")
    index_url = url_for("index")
    login_url = url_for("auth.login")
    register_mfr_url = url_for("auth.register_manufacturer")

    visual = _auth_visual("Customer onboarding", "Source manufacturing for your next production run.")
    body = f"""<div class="auth-page">
{visual}

  <div class="auth-page__form-wrap">
    <div class="auth-card">
      <div class="auth-card__header">
        <div>
          <div class="eyebrow eyebrow--dark">Get started</div>
          <h1>Create customer account</h1>
        </div>
        <a class="text-link" href="{index_url}">Back to home</a>
      </div>

      {flash_messages()}

      <form method="POST" action="{register_url}" class="auth-form">
        <div class="form-group">
          <label class="form-label" for="full_name">Full Name</label>
          <input class="form-input" type="text" id="full_name" name="full_name" required value="{e(form.get('full_name', '') or '')}" />
        </div>
        <div class="form-group">
          <label class="form-label" for="email">Email</label>
          <input class="form-input" type="email" id="email" name="email" required value="{e(form.get('email', '') or '')}" />
        </div>
        <div class="form-group">
          <label class="form-label" for="phone">Phone (optional)</label>
          <input class="form-input" type="tel" id="phone" name="phone" value="{e(form.get('phone', '') or '')}" />
        </div>
        <div class="form-group">
          <label class="form-label" for="password">Password</label>
          <input class="form-input" type="password" id="password" name="password" required />
        </div>
        <button class="btn btn-primary" type="submit">Register</button>
      </form>

      <div class="auth-card__links">
        <p>Already have an account? <a href="{login_url}">Login</a></p>
        <p>Looking to manufacture? <a href="{register_mfr_url}">Register as manufacturer</a></p>
      </div>
    </div>
  </div>
</div>"""

    return base_layout(title="Register | 3D Marketplace", body_content=body)


def register_manufacturer_page(form=None, **kwargs):
    form = form or {}
    register_mfr_url = url_for("auth.register_manufacturer")
    index_url = url_for("index")
    login_url = url_for("auth.login")
    register_url = url_for("auth.register")

    visual = _auth_visual("Manufacturer access", "Bring your shop capacity to qualified production requests.")
    body = f"""<div class="auth-page">
{visual}

  <div class="auth-page__form-wrap">
    <div class="auth-card">
      <div class="auth-card__header">
        <div>
          <div class="eyebrow eyebrow--dark">Manufacturing network</div>
          <h1>Register as manufacturer</h1>
        </div>
        <a class="text-link" href="{index_url}">Back to home</a>
      </div>

      {flash_messages()}

      <form method="POST" action="{register_mfr_url}" class="auth-form">
        <div class="form-group">
          <label class="form-label" for="full_name">Full Name</label>
          <input class="form-input" type="text" id="full_name" name="full_name" required value="{e(form.get('full_name', '') or '')}" />
        </div>
        <div class="form-group">
          <label class="form-label" for="business_name">Business Name</label>
          <input class="form-input" type="text" id="business_name" name="business_name" required value="{e(form.get('business_name', '') or '')}" />
        </div>
        <div class="form-group">
          <label class="form-label" for="email">Email</label>
          <input class="form-input" type="email" id="email" name="email" required value="{e(form.get('email', '') or '')}" />
        </div>
        <div class="form-group">
          <label class="form-label" for="phone">Phone (optional)</label>
          <input class="form-input" type="tel" id="phone" name="phone" value="{e(form.get('phone', '') or '')}" />
        </div>
        <div class="form-group">
          <label class="form-label" for="password">Password</label>
          <input class="form-input" type="password" id="password" name="password" required />
        </div>
        <button class="btn btn-primary" type="submit">Register</button>
      </form>

      <div class="auth-card__links">
        <p>Already have an account? <a href="{login_url}">Login</a></p>
        <p>Looking to order parts? <a href="{register_url}">Create customer account</a></p>
      </div>
    </div>
  </div>
</div>"""

    return base_layout(title="Register Manufacturer | 3D Marketplace", body_content=body)