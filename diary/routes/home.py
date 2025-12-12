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
    conn = get_db()
    with conn.cursor() as cur:
        if tag:
            # Join through diary_tags -> tags and only return entries matching the tag
            cur.execute(
                """
                SELECT d.id, d.title, d.content, d.created_at,
                       GROUP_CONCAT(t.name SEPARATOR ',') AS tags
                FROM diary d
                LEFT JOIN diary_tags dt ON dt.diary_id = d.id
                LEFT JOIN tags t ON t.id = dt.tag_id
                WHERE t.name = %s
                GROUP BY d.id
                ORDER BY d.created_at DESC
                """,
                (tag,)
            )
        else:
            cur.execute(
                """
                SELECT d.id, d.title, d.content, d.created_at,
                       GROUP_CONCAT(t.name SEPARATOR ',') AS tags
                FROM diary d
                LEFT JOIN diary_tags dt ON dt.diary_id = d.id
                LEFT JOIN tags t ON t.id = dt.tag_id
                GROUP BY d.id
                ORDER BY d.created_at DESC
                """
            )
        entries = cur.fetchall()

    return render_template('home/preview.html', entries=entries, tag=tag)


@bp.route('/title')
def title():
    selected_tag = request.args.get('tag')
    conn = get_db()
    with conn.cursor() as cur:
        if selected_tag:
            # Select entries that have the selected tag (via EXISTS), but do not
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
                """,
                (selected_tag,)
            )
        else:
            cur.execute(
                """
                SELECT d.id, d.title, GROUP_CONCAT(t.name SEPARATOR ',') AS tags
                FROM diary d
                LEFT JOIN diary_tags dt ON dt.diary_id = d.id
                LEFT JOIN tags t ON t.id = dt.tag_id
                GROUP BY d.id
                ORDER BY d.created_at DESC
                """
            )
        entries = cur.fetchall()

        # Fetch all tags for the filter select
        cur.execute('SELECT id, name FROM tags ORDER BY name')
        all_tags = cur.fetchall()

    return render_template('home/title.html', entries=entries, tags=all_tags, selected_tag=selected_tag)