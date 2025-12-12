"""Database helpers for the `diary` Flask application.

This module configures a persistent MySQL connection stored on `g.db`.
It registers a teardown handler with the Flask app so connections are
closed at the end of requests. The implementation will attempt to
connect to a database named `diary` and create it if it does not exist.

Credentials must be provided by the application configuration or
environment (see `create_app()` in `diary/__init__.py`). Do not put
secrets in source files.

Note: This requires a running MySQL server and the `PyMySQL` package.
"""

import pymysql
from flask import current_app, g
from pymysql.err import OperationalError
from typing import Optional
import click
from flask.cli import with_appcontext
import os
from os import path


def get_db():
    """Return a MySQL connection, creating it and the database if needed.

    The connection is stored on `g.db` for the request lifecycle.
    Raises a RuntimeError when DB credentials are missing so callers
    get a clear message instead of accidental anonymous connections.
    """
    if 'db' in g:
        return g.db

    app = current_app._get_current_object()
    host = app.config.get('DB_HOST', 'localhost')
    port = int(app.config.get('DB_PORT', 3306))
    user = app.config.get('DB_USER')
    password = app.config.get('DB_PASSWORD')
    db_name = app.config.get('DB_NAME', 'diary')

    if not user or not password:
        raise RuntimeError(
            'Database credentials are not configured. Set `DB_USER` and `DB_PASSWORD` in the instance config or environment.'
        )

    # Try connecting directly to the requested database
    try:
        conn = pymysql.connect(host=host, port=port, user=user, password=password, db=db_name, cursorclass=pymysql.cursors.DictCursor, autocommit=True)
    except OperationalError as exc:
        # If the database does not exist, create it and reconnect.
        # Other errors are re-raised.
        msg = str(exc)
        if 'Unknown database' in msg or "doesn't exist" in msg:
            # Connect without database to create it
            admin_conn: Optional[pymysql.connections.Connection] = None
            try:
                admin_conn = pymysql.connect(host=host, port=port, user=user, password=password, cursorclass=pymysql.cursors.DictCursor, autocommit=True)
                with admin_conn.cursor() as cur:
                    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            finally:
                if admin_conn:
                    admin_conn.close()

            # Reconnect to the newly created database
            conn = pymysql.connect(host=host, port=port, user=user, password=password, db=db_name, cursorclass=pymysql.cursors.DictCursor, autocommit=True)
        else:
            raise

    g.db = conn
    return conn


def close_db(e=None):
    """Close the MySQL connection stored on `g` if present."""
    db = g.pop('db', None)

    if db is not None:
        try:
            db.close()
        except Exception:
            pass


def init_db(app=None):
    """Initialize DB helpers for the given Flask app.

    This registers a teardown handler that closes DB connections and
    provides a convenient place to expose CLI commands later. Secret
    values (DB_USER/DB_PASSWORD) should be set via environment or
    `instance/config.py` and are deliberately not defaulted here.
    """
    if app is None:
        # Backwards compatibility: allow calling without app to return the function
        # Use the module-level `current_app` (avoid re-importing into the local scope
        # which can cause closure issues for nested functions).
        app = current_app

    # Default configuration values for non-secret options
    app.config.setdefault('DB_HOST', 'localhost')
    app.config.setdefault('DB_PORT', 3306)
    app.config.setdefault('DB_NAME', 'diary')

    app.teardown_appcontext(close_db)

    # Register a Flask CLI command to initialize schema from instance/schema.sql
    @click.command('init-db')
    @with_appcontext
    def init_db_command():
        """Initialize the database schema from `instance/schema.sql`.

        The SQL file is expected to contain one or more statements separated
        by semicolons. This command will execute each non-empty statement.
        """
        schema_path = path.join(current_app.instance_path, 'schema.sql')
        if not path.exists(schema_path):
            click.echo(f'No schema file found at {schema_path}')
            return

        sql = ''
        with open(schema_path, 'r', encoding='utf-8') as fh:
            sql = fh.read()

        conn = get_db()
        with conn.cursor() as cur:
            # Naive split by semicolon; sufficient for simple schema files.
            for stmt in (s.strip() for s in sql.split(';')):
                if not stmt:
                    continue
                cur.execute(stmt)

        click.echo('Initialized the database schema.')

    app.cli.add_command(init_db_command)
