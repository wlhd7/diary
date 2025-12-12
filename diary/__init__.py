from flask import Flask
from .db import init_db
from os import makedirs
import os
from .routes import init_routes


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Start with an empty mapping, allow instance/config.py to override
    app.config.from_mapping()

    try:
        makedirs(app.instance_path)
    except OSError:
        pass

    # Load instance config (untracked, environment specific)
    app.config.from_pyfile('config.py', silent=True)

    # Allow environment variables to override instance config
    if os.environ.get('DB_HOST'):
        app.config['DB_HOST'] = os.environ['DB_HOST']
    if os.environ.get('DB_PORT'):
        try:
            app.config['DB_PORT'] = int(os.environ['DB_PORT'])
        except ValueError:
            app.config['DB_PORT'] = app.config.get('DB_PORT', 3306)
    if os.environ.get('DB_USER'):
        app.config['DB_USER'] = os.environ['DB_USER']
    if os.environ.get('DB_PASSWORD'):
        app.config['DB_PASSWORD'] = os.environ['DB_PASSWORD']
    if os.environ.get('DB_NAME'):
        app.config['DB_NAME'] = os.environ['DB_NAME']

    # Allow SECRET_KEY to be provided via instance config or overridden by environment
    # Order: instance/config.py -> environment -> default (None)
    if os.environ.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

    app.config.setdefault('SECRET_KEY', None)

    # sane defaults for non-secret values
    app.config.setdefault('DB_HOST', 'localhost')
    app.config.setdefault('DB_PORT', 3306)
    app.config.setdefault('DB_NAME', 'diary')

    # Initialize database integrations (register teardown handlers, CLI helpers)
    init_db(app)

    init_routes(app)

    return app