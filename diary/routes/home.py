from flask import Blueprint, render_template, request
from diary.db import get_db

bp = Blueprint('home', __name__)


@bp.route('/preview')
def preview():
    """Show recent diary entries. If `?tag=<name>` is provided, filter by tag.

    Each returned row includes an optional `tags` column containing a
    comma-separated list of tag names (or None).
    """
    tag = request.args.get('tag')
    try:
        page = int(request.args.get('page', '1'))
    except ValueError:
        page = 1
    if page < 1:
        page = 1
    per_page = 10
    offset = (page - 1) * per_page

    conn = get_db()
    with conn.cursor() as cur:
        if tag:
            # Count matching entries for pagination (use DISTINCT to avoid duplicate rows)
            cur.execute(
                """
                SELECT COUNT(DISTINCT d.id) AS cnt
                FROM diary d
                JOIN diary_tags dt2 ON dt2.diary_id = d.id
                JOIN tags t2 ON t2.id = dt2.tag_id
                WHERE t2.name = %s
                """,
                (tag,)
            )
            total = cur.fetchone()['cnt']

            # Select paginated entries that have the selected tag, but include all tags in GROUP_CONCAT
            cur.execute(
                """
                SELECT d.id, d.title, d.content, d.created_at,
                       GROUP_CONCAT(t.name SEPARATOR ',') AS tags
                FROM diary d
                LEFT JOIN diary_tags dt ON dt.diary_id = d.id
                LEFT JOIN tags t ON t.id = dt.tag_id
                WHERE EXISTS (
                  SELECT 1 FROM diary_tags dt2
                  JOIN tags t2 ON t2.id = dt2.tag_id
                  WHERE dt2.diary_id = d.id AND t2.name = %s
                )
                GROUP BY d.id
                ORDER BY d.created_at DESC
                LIMIT %s OFFSET %s
                """,
                (tag, per_page, offset),
            )
        else:
            cur.execute('SELECT COUNT(*) AS cnt FROM diary')
            total = cur.fetchone()['cnt']

            cur.execute(
                """
                SELECT d.id, d.title, d.content, d.created_at,
                       GROUP_CONCAT(t.name SEPARATOR ',') AS tags
                FROM diary d
                LEFT JOIN diary_tags dt ON dt.diary_id = d.id
                LEFT JOIN tags t ON t.id = dt.tag_id
                GROUP BY d.id
                ORDER BY d.created_at DESC
                LIMIT %s OFFSET %s
                """,
                (per_page, offset),
            )
        entries = cur.fetchall()

    total_pages = max(1, (int(total) + per_page - 1) // per_page)
    if page > total_pages:
        page = total_pages

    return render_template('home/preview.html', entries=entries, tag=tag, page=page, total_pages=total_pages, per_page=per_page, total=total)


@bp.route('/title')
def title():
    selected_tag = request.args.get('tag')
    # Pagination
    try:
        page = int(request.args.get('page', '1'))
    except ValueError:
        page = 1
    if page < 1:
        page = 1
    per_page = 20
    offset = (page - 1) * per_page
    conn = get_db()
    with conn.cursor() as cur:
        if selected_tag:
            # Count matching entries for pagination
            cur.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM diary d
                WHERE EXISTS (
                  SELECT 1 FROM diary_tags dt2
                  JOIN tags t2 ON t2.id = dt2.tag_id
                  WHERE dt2.diary_id = d.id AND t2.name = %s
                )
                """,
                (selected_tag,)
            )
            total = cur.fetchone()['cnt']

            # Select paginated entries that have the selected tag (via EXISTS), but do not
            # filter the outer JOIN on tags so GROUP_CONCAT includes all tags.
            cur.execute(
                """
                SELECT d.id, d.title, GROUP_CONCAT(t.name SEPARATOR ',') AS tags
                FROM diary d
                LEFT JOIN diary_tags dt ON dt.diary_id = d.id
                LEFT JOIN tags t ON t.id = dt.tag_id
                WHERE EXISTS (
                  SELECT 1 FROM diary_tags dt2
                  JOIN tags t2 ON t2.id = dt2.tag_id
                  WHERE dt2.diary_id = d.id AND t2.name = %s
                )
                GROUP BY d.id
                ORDER BY d.created_at DESC
                LIMIT %s OFFSET %s
                """,
                (selected_tag, per_page, offset)
            )
        else:
            # Count total entries for pagination
            cur.execute('SELECT COUNT(*) AS cnt FROM diary')
            total = cur.fetchone()['cnt']

            cur.execute(
                """
                SELECT d.id, d.title, GROUP_CONCAT(t.name SEPARATOR ',') AS tags
                FROM diary d
                LEFT JOIN diary_tags dt ON dt.diary_id = d.id
                LEFT JOIN tags t ON t.id = dt.tag_id
                GROUP BY d.id
                ORDER BY d.created_at DESC
                LIMIT %s OFFSET %s
                """,
                (per_page, offset)
            )
        entries = cur.fetchall()

        # Fetch all tags for the filter select
        cur.execute('SELECT id, name FROM tags ORDER BY name')
        all_tags = cur.fetchall()

    # Compute pagination values
    total_pages = max(1, (int(total) + per_page - 1) // per_page)
    if page > total_pages:
        page = total_pages

    return render_template(
        'home/title.html',
        entries=entries,
        tags=all_tags,
        selected_tag=selected_tag,
        page=page,
        total_pages=total_pages,
        per_page=per_page,
        total=total,
    )