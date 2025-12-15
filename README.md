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
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Set Flask app factory and (optionally) dev mode:
```bash
export FLASK_APP=diary:create_app
export FLASK_ENV=development    # optional
```
4. Provide runtime config in `instance/config.py` or environment variables. Minimal keys used by the app include:
```
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
# or run via gunicorn in production
```

Notes for contributors
- Do not commit secrets — use `instance/config.py` locally or environment variables. `instance/` is gitignored for secrets.
- The project does not include a migration tool (Alembic). If you change the schema, update `instance/schema.sql` and document changes.

Removed container files
- This repository previously included Docker/compose files; they have been removed. Ask the repo owner for current deployment instructions if you need container-based workflows.

Need help?
- I can add an `instance/config.py.example`, a short README section on deploying with a reverse proxy, or an Alembic migration setup — tell me which you'd prefer.
