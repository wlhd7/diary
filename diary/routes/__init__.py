from flask import request, session, redirect, url_for
from .home import bp as home_bp
from .auth import bp as auth_bp
from .diary import bp as diary_bp
from .tags import bp as tags_bp

bps = [home_bp, auth_bp, diary_bp, tags_bp]

def init_routes(app):
    for bp in bps:
        app.register_blueprint(bp)
    
    app.add_url_rule('/', endpoint='home.preview')

    # Enforce login for all endpoints by default, with an allowlist.
    # Order of allowlist resolution: `AUTH_PUBLIC_ENDPOINTS` from config -> defaults
    @app.before_request
    def require_login_globally():
        endpoint = request.endpoint
        if endpoint is None:
            return

        # Default public endpoints
        default_allow = {'auth.login', 'auth.register', 'static'}

        # Merge configured public endpoints
        allowlist = set(app.config.get('AUTH_PUBLIC_ENDPOINTS', [])) | default_allow

        if endpoint in allowlist:
            return

        if session.get('user_id') is None:
            return redirect(url_for('auth.login', next=request.path))