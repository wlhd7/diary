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
                # detect closure table presence; if present use it, otherwise build
                # a recursive CTE per keyword to include descendant tags
                cur.execute(
                    "SELECT COUNT(*) AS cnt FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = %s",
                    ("diary_tags_closure",)
                )
                closure_exists = cur.fetchone()['cnt'] > 0

                if closure_exists:
                    where_clauses = []
                    params = []
                    for kw in keywords:
                        like = f"%{kw}%"
                        where_clauses.append(
                            "(d.title LIKE %s OR d.content LIKE %s OR EXISTS (SELECT 1 FROM diary_tags_closure dt2 JOIN tags t2 ON t2.id = dt2.tag_id WHERE dt2.diary_id = d.id AND t2.name LIKE %s))"
                        )
                        params.extend([like, like, like])

                    where_sql = " AND ".join(where_clauses)
                    sql = f"""
                    SELECT d.id, d.title, d.content, d.created_at,
                        GROUP_CONCAT(t_all.name SEPARATOR ',') AS tags
                    FROM diary d
                    LEFT JOIN diary_tags dt_all ON dt_all.diary_id = d.id
                    LEFT JOIN tags t_all ON dt_all.tag_id = t_all.id
                    WHERE {where_sql}
                    GROUP BY d.id
                    ORDER BY d.created_at DESC
                    """
                    cur.execute(sql, tuple(params))
                else:
                    # Build recursive CTEs: one per keyword to gather matching tags and their descendants
                    cte_defs = []
                    where_parts = []
                    cte_params = []
                    where_params = []
                    for i, kw in enumerate(keywords, start=1):
                        like = f"%{kw}%"
                        cte_name = f"tag_desc_{i}"
                        cte_defs.append(
                            f"{cte_name} AS (SELECT id FROM tags WHERE name LIKE %s UNION ALL SELECT t.id FROM tags t JOIN {cte_name} ON t.parent_id = {cte_name}.id)"
                        )
                        cte_params.append(like)

                        # For each keyword, match title/content OR existence of a tag in the CTE
                        where_parts.append(
                            f"(d.title LIKE %s OR d.content LIKE %s OR EXISTS (SELECT 1 FROM diary_tags dt2 WHERE dt2.diary_id = d.id AND dt2.tag_id IN (SELECT id FROM {cte_name})))"
                        )
                        where_params.extend([like, like])

                    where_sql = " AND ".join(where_parts)
                    cte_sql = "WITH RECURSIVE " + ", ".join(cte_defs)

                    sql = f"""
                    {cte_sql}
                    SELECT d.id, d.title, d.content, d.created_at,
                        GROUP_CONCAT(t.name SEPARATOR ',') AS tags
                    FROM diary d
                    LEFT JOIN diary_tags dt ON d.id = dt.diary_id
                    LEFT JOIN tags t ON t.id = dt.tag_id
                    WHERE {where_sql}
                    GROUP BY d.id
                    ORDER BY d.created_at DESC
                    """
                    # parameter order: CTE seeds, then where title/content params
                    params = tuple(cte_params + where_params)
                    cur.execute(sql, params)

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
