"""
auth_pages.py — Pure Python pyui functions for auth pages.
No Jinja2. All user/form values escaped with e(). HTML structure preserved from templates.
"""
from flask import url_for
from app.pyui.helpers import e, flash_messages
from app.pyui.layout import base_layout


def _auth_visual(eyebrow, heading):
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
        <span></span><span></span><span></span><span></span>
        <span></span><span></span><span></span><span></span>
        <span></span><span></span><span></span><span></span>
      </div>
    </div>
  </div>"""


def login_page(next_url=None, email="", **kwargs):
    login_url = url_for("auth.login")
    index_url = url_for("index")
    register_url = url_for("auth.register")
    register_mfr_url = url_for("auth.register_manufacturer")

    next_input = f'<input type="hidden" name="next" value="{e(next_url)}" />' if next_url else ""

    visual = _auth_visual("Production network", "Precision manufacturing supply chain.")
    body = f"""<div class="auth-page">
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