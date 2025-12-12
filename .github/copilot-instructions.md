<!-- Copilot / AI Agent instructions for the `diary` repository -->
# Purpose
This file gives concise, actionable guidance for AI coding agents working in this repository so they can be productive immediately.

# Big picture
- Minimal Flask application using an application factory in `diary/__init__.py` (function `create_app`).
- The app creates and relies on the `instance/` directory for instance-specific configuration and runtime files.
- Database initialization is expected to live in `diary/db.py` (`init_db()` exists but is currently a placeholder).

# Key files to inspect first
- `diary/__init__.py` — app factory, creates `instance_path` and calls `app.config.from_mapping()`.
- `diary/db.py` — contains `init_db()`; implement or update the DB connection logic here.
- `instance/` — instance configuration and runtime files belong here (created by the app at runtime).

# Project-specific conventions and patterns
- Use the Flask application factory pattern (`create_app`) — code should avoid importing a global `app`.
- Store instance-specific secrets/config in `instance/` and access via `app.instance_path` or `app.config`.
- Keep changes minimal and localized. The repository is intentionally small: prefer small, well-scoped edits rather than broad refactors.

# Developer workflows (commands an agent can run locally)
- Run the app (development):
  - `export FLASK_APP=diary:create_app`
  - `export FLASK_ENV=development` (optional)
  - `flask run`
- Alternatively run by Python module: `python -m flask run` after setting `FLASK_APP`.

# Integration points & external dependencies
- There are no declared external dependency manifests (no `requirements.txt` or `pyproject.toml`) in the repo. Assume only the standard library and `Flask` are used based on source imports.

# Concrete examples and patterns to follow
- To initialize a local SQLite database, implement `init_db()` in `diary/db.py`. Example (illustrative — adapt to tests or user requirements):

```py
import sqlite3
from flask import current_app, g
from os import path

def init_db():
    db_path = path.join(current_app.instance_path, 'diary.sqlite')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    g.db = conn
    return conn
```

- When changing configuration, prefer adding files under `instance/` (the app creates this path on startup).

# Editing & PR guidance for AI agents
- Merge behavior: if `.github/copilot-instructions.md` already exists, preserve existing high-value guidance and append or replace only outdated sections.
- Keep commits small and focused. Use descriptive commit messages like `impl: implement init_db using sqlite in instance path`.

# What not to assume
- Do not assume any CI, test runner, or package manager is present — none are discoverable in the repository root.
- Do not add heavy new frameworks or change project layout without explicit instruction from the user.

# Next steps for an AI agent
- Start by implementing or improving `diary/db.py` only if the user requested DB features.
- If you modify runtime behavior, update or create example run commands in this file and ask the user to run the app locally.

If any of these sections are unclear or you'd like additional examples (tests, Dockerfile, dependency manifest), tell me which area to expand. 
