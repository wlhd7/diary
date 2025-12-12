from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from diary.db import get_db
from pymysql.err import IntegrityError
from urllib.parse import urlparse, urljoin


bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Simple username/password login.

    This implementation is intentionally minimal: it accepts any
    non-empty username/password and stores `user_id` in the session.
    Replace with real credential checks against the database as needed.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        next_url = request.form.get('next') or url_for('home.preview')

        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('auth/login.html', next=next_url)

        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT id, password_hash FROM users WHERE username=%s", (username,))
            user = cur.fetchone()

        if user is None or not check_password_hash(user.get('password_hash', ''), password):
            flash('Invalid username or password.', 'error')
            return render_template('auth/login.html', next=next_url)

        session.clear()
        session['user_id'] = user['id']
        session['username'] = username
        flash('Logged in successfully.', 'success')
        # Prevent open redirects — ensure `next_url` is local to this app
        def is_safe_url(target):
            host_url = request.host_url
            ref_url = urlparse(host_url)
            test_url = urlparse(urljoin(host_url, target))
            return (test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc)

        if not is_safe_url(next_url):
            next_url = url_for('home.preview')

        return redirect(next_url)

    # GET
    next_url = request.args.get('next')
    # If the next param is present but not safe, ignore it
    if next_url and not urlparse(next_url).netloc:
        safe_next = next_url
    else:
        safe_next = None
    return render_template('auth/login.html', next=safe_next)


@bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    return redirect(url_for('auth.login'))
    """Minimal registration placeholder.

    This does not persist users; it's provided as a stub so the
    `auth.register` endpoint exists for allowlists. Implement DB-backed
    registration if you need persistent users.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('auth/register.html')

        conn = get_db()
        try:
            pw_hash = generate_password_hash(password)
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                    (username, pw_hash),
                )
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except IntegrityError:
            flash('Username already exists.', 'error')
            return render_template('auth/register.html')

    return render_template('auth/register.html')