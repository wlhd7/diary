from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from diary.db import get_db

bp = Blueprint('search', __name__, url_prefix='/search')


@bp.route('/', methods=['GET', 'POST'])
def index():
    """Search diary entries by title, content, or tag name.

    - GET: show form and optional `q` results
    - POST: accept form submission and redirect to GET for bookmarking
    """
    q = ''
    results = []

    if request.method == 'POST':
        q = request.form.get('q', '').strip()
        return redirect(url_for('search.index', q=q))

    # GET handling
    q = request.args.get('q', '').strip()
    if q:
        # Record search in session-backed history (most-recent first, unique, cap 20)
        history = session.get('search_history', [])
        if q in history:
            history.remove(q)
        history.insert(0, q)
        session['search_history'] = history[:20]

        # Support multiple keywords separated by whitespace; require all keywords (AND)
        keywords = [k for k in q.split() if k]
        conn = get_db()
        with conn.cursor() as cur:
            if keywords:
                where_clauses = []
                params = []
                for kw in keywords:
                    like = f"%{kw}%"
                    where_clauses.append("(d.title LIKE %s OR d.content LIKE %s OR t.name LIKE %s)")
                    params.extend([like, like, like])

                where_sql = " AND ".join(where_clauses)
                sql = f"""
                SELECT d.id, d.title, d.content, d.created_at,
                    GROUP_CONCAT(t.name SEPARATOR ',') AS tags
                FROM diary d
                LEFT JOIN diary_tags_closure dt ON d.id = dt.diary_id
                LEFT JOIN tags t ON dt.tag_id = t.id
                WHERE {where_sql}
                GROUP BY d.id
                ORDER BY d.created_at DESC
                """
                cur.execute(sql, tuple(params))
                results = cur.fetchall()
            else:
                results = []
        # Persist the search term and increment its count in `search_history`
        # only when the search actually returned results.
        if results:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO search_history (term, count, last_searched) VALUES (%s, 1, CURRENT_TIMESTAMP) "
                        "ON DUPLICATE KEY UPDATE count = count + 1, last_searched = CURRENT_TIMESTAMP",
                        (q,)
                    )
            except Exception:
                # Non-fatal: ignore DB errors so search still works
                pass

    return render_template('search/index.html', q=q, results=results)

@bp.route('/history')
def history():
    # Support optional filtering and ordering via query params:
    # - filter: substring match on `term`
    # - order: 'usage' (count desc) or 'time' (last_searched desc)
    filter_term = request.args.get('filter', '').strip()
    order = request.args.get('order', 'usage')

    conn = get_db()
    params = []
    where_sql = ''
    if filter_term:
        where_sql = 'WHERE term LIKE %s'
        params.append(f"%{filter_term}%")

    if order == 'time':
        order_sql = 'ORDER BY last_searched DESC, count DESC'
    else:
        order_sql = 'ORDER BY count DESC, last_searched DESC'

    with conn.cursor() as cur:
        sql = f"SELECT term, count, last_searched FROM search_history {where_sql} {order_sql}"
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()

    return render_template('search/history.html', history=rows, filter=filter_term, order=order)


@bp.route('/history/delete', methods=['POST'])
def delete_history_term():
    """Delete a single search term from the persistent `search_history` table."""
    term = request.form.get('term')
    if not term:
        flash('No term specified.', 'error')
        return redirect(url_for('search.history'))

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM search_history WHERE term = %s', (term,))
    except Exception:
        flash('Could not delete search term.', 'error')
        return redirect(url_for('search.history'))

    flash(f'Removed search "{term}".', 'success')
    return redirect(url_for('search.history'))
