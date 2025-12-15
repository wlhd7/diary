<!-- Copilot / AI Agent instructions for the `diary` repository -->
# Purpose
Concise, actionable guidance for AI coding agents working in this repository so they can be productive immediately.

## Big picture
- Minimal Flask app using an application factory: see `diary/__init__.py` (`create_app`).
- Configuration and runtime secrets live under `instance/` (do not commit secrets).
- Database is MySQL accessed via `PyMySQL`; DB helpers are in `diary/db.py` and the project exposes a `flask init-db` CLI that executes `instance/schema.sql`.
- Routes are organized as blueprints in `diary/routes/`: `auth.py`, `diary.py`, `home.py`, `tags.py`. Templates live under `templates/` grouped by blueprint.

## Key files to inspect first
- `diary/__init__.py` — application factory, blueprint registration, loads `instance/config.py` if present.
- `diary/db.py` — `get_db()`, `close_db()`, `init_db(app)`; follow its API when changing DB behavior.
- `diary/routes/` — blueprint handlers and URL structure (auth, diary, home, tags).
- `instance/schema.sql` — canonical SQL schema applied by `flask init-db`.
- `requirements.txt`, `Dockerfile`, `docker-compose.yml`, `deploy/nginx.conf` — runtime & deployment material.

## How to run & common developer commands
- Local development (from repo root):
  - Set the app factory: `export FLASK_APP=diary:create_app`
  - Optional dev mode: `export FLASK_ENV=development`
  - Run: `flask run`
- Initialize the DB (runs SQL in `instance/schema.sql` using app config):
  - `flask init-db`
- Docker / container workflows:
  - Populate `instance/.env` (runtime DB credentials, SECRET_KEY) referenced by `docker-compose.yml`.
  - Build: `docker compose build`
  - Start: `docker compose up -d`
  - Init DB inside container: `docker compose run --rm web flask init-db`

## Project-specific conventions & patterns
- Application factory pattern only — avoid importing a global `app` object. Use `create_app()` to construct app with config.
- `instance/` is authoritative for per-deployment configuration. Don't commit secrets; prefer `instance/.env` or `instance/config.py` excluded by `.gitignore`.
- Routes are organized as small blueprints: add new pages by creating a file in `diary/routes/`, registering a Blueprint there, and importing in `diary/__init__.py`.
- Templates mirror blueprints: add `templates/<blueprint>/...` for view templates (e.g., `templates/diary/index.html`).

## Data flow & integration points
- Web requests → blueprint view in `diary/routes/*` → DB helpers in `diary/db.py` → MySQL.
- `flask init-db` opens a MySQL connection using config in `app.config` and applies `instance/schema.sql` statements.
- The app relies on environment variables and `instance/config.py` for DB connection strings, secret keys, and other runtime settings.

## Dependencies & noteworthy libraries
- `Flask` for the web framework.
- `PyMySQL` for MySQL connections; `cryptography` present to support some MySQL auth plugins.
- No database migration tool (Alembic) is present — schema changes are applied manually via `instance/schema.sql`.

## Editing / PR guidance for AI agents
- Keep changes minimal and focused: small PRs are preferred.
- When modifying DB schema, update `instance/schema.sql` and prefer `flask init-db` for applying the schema (document changes in the PR).
- Do not commit secrets. Use `instance/.env` or instruct the repo owner to add `instance/config.py` locally.

## Troubleshooting tips
- If DB connection fails, verify `app.config['DATABASE_*']` values in `instance/config.py` or `.env` and check MySQL accessibility.
- If a template or blueprint isn't found, confirm the blueprint is registered in `create_app()` in `diary/__init__.py` and names match templates subfolders.

## When to ask the repo owner
- Before adding new heavy frameworks (ORMs, migrations, or task queues).
- Before changing the public API or directory layout.

If you'd like, I can add a short `instance/config.py.example`, or wire an Alembic migration setup. Any section you want expanded or clarified?
