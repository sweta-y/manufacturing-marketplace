# Manufacturing Marketplace

A manufacturing marketplace web app connecting customers with manufacturers for custom part requests, production workflows, and order tracking.

## Tech stack

- Flask + Jinja2 for server-rendered HTML pages
- Plain HTML forms (no JavaScript-driven app flow)
- PostgreSQL
- SQLAlchemy

## Project structure

- backend/app: Flask application package
  - routes/: customer, manufacturer, admin, and auth routes
  - templates/: Jinja2 templates for each portal and shared layout
  - static/: CSS/assets
- backend/seed/: seed and reset scripts for local/demo data
- backend/uploads/: uploaded design files for customer requests
- database/schema.sql: database schema
- frontend/: static/demo front-end files

## Setup

1. Clone the repository.
2. Create a virtual environment:

```bash
python -m venv venv
```

3. Activate it on Windows:

```powershell
.\venv\Scripts\activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Set up PostgreSQL and configure the database connection. The app reads environment variables from a .env file and uses the settings in backend/app/config.py:

- DB_HOST
- DB_PORT
- DB_NAME
- DB_USER
- DB_PASSWORD
- SECRET_KEY

Example:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=manufacturing_marketplace
DB_USER=postgres
DB_PASSWORD=your_password
SECRET_KEY=change-me
```

6. Create the database and initialize the schema if needed.
7. Seed demo data if you want the included sample users and orders:

```bash
python backend/seed/reset_and_seed.py
```

## Run locally

From the backend directory:

```bash
python run.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Supported user roles

- Customer
- Manufacturer
- Admin

## Cost Estimator

The app includes a C-based cost estimator that calculates manufacturing costs and time based on:
- Manufacturing process (CNC Machining, 3D Printing, Laser Cutting)
- Material type (Aluminum, Steel, PLA, Acrylic)
- Quantity requested

### Using the estimator

The cost estimator is automatically called when customers configure their orders. It shows:
- Estimated total cost
- Estimated production time (in hours)

**Currently:** The app uses a Python fallback estimator built with the same logic as the C version, so cost estimates work immediately.

### Compiling the C version (optional, for better performance)

For a faster, compiled C estimator:

1. Install MinGW-w64 gcc:
   - Download: https://www.mingw-w64.org/
   - Or: `choco install mingw` (via Chocolatey)
   - Or: `winget install mingw` (Windows 11+)

2. Compile:
   ```bash
   cd backend/c_module
   .\compile.bat
   ```

3. The compiled `cost_estimator.exe` will be automatically used instead of the Python fallback.

