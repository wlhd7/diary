# Diary

Minimal Flask diary application (application-factory pattern).

Key points
- App factory: `diary:create_app()` — see `diary/__init__.py`.
- DB: MySQL via `PyMySQL`. Helpers in `diary/db.py`. Canonical schema in `instance/schema.sql`.
- Routes: organized as blueprints in `diary/routes/` (auth, diary, home, tags).

Quick start (local development)
1. Create a Python venv and activate it (recommended):
```bash
python -m venv .venv
source .venv/bin/activate
```
2. Install runtime dependencies:
```bash
pip install -r requirements.txt
```
3. Set Flask app factory and (optionally) dev mode:
```bash
export FLASK_APP=diary:create_app
export FLASK_ENV=development    # optional
```
4. Provide runtime config in `instance/config.py` or environment variables. Minimal keys used by the app include:
```py
# instance/config.py (example)
SECRET_KEY = 'replace-me'
DATABASE_HOST = '127.0.0.1'
DATABASE_PORT = 3306
DATABASE_USER = 'diary'
DATABASE_PASSWORD = 'secret'
DATABASE_NAME = 'diary'
```
5. Initialize the database (will execute `instance/schema.sql`):
```bash
flask init-db
```
6. Run the app locally:
```bash
flask run
```

Packaging & production install
- This repository includes a `pyproject.toml` so you can build a wheel and install into a dedicated venv for production or CI:
```bash
python -m pip install --upgrade build
python -m build    # creates dist/*.whl
python -m venv /opt/diary/.venv
/opt/diary/.venv/bin/pip install dist/diary-*.whl
```
- Or for development editable install:
```bash
pip install -e .
```

Gunicorn + reverse proxy (production)
- Preferred: run Gunicorn in a venv and front it with Nginx. Example systemd and Nginx snippets are in the `deploy/` folder (`deploy/diary.service`, `deploy/nginx.conf`).
- A minimal systemd unit and Nginx site are provided as examples — adapt paths, user, and domain before use.

Notes for contributors
- Do not commit secrets — use `instance/config.py` locally or environment variables. `instance/` is gitignored for secrets.
- The project does not include an automated migration tool (Alembic). If you change the schema, update `instance/schema.sql` and document the change.

Need help?
- I can add CI steps to build/publish wheels, create a `instance/config.py.example`, or set up Alembic migrations. Which would you prefer?
