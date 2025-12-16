from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from diary.db import get_db


bp = Blueprint('diary', __name__, url_prefix='/diary')


@bp.route('/new', methods=['GET', 'POST'])
def new():
    """Create a new diary entry (requires authentication).

    The route accepts `title` and `content` and inserts a row into the
    `diary` table. On success the user is redirected to `home.preview`.
    """
    # Simple guard in case global auth is not enabled
    if session.get('user_id') is None:
        return redirect(url_for('auth.login', next=request.path))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        # Collect tag ids submitted from the form (multiple-select)
        selected_tags = request.form.getlist('tags')

        if not title:
            flash('Title is required.', 'error')
            return render_template('diary/new.html', title=title, content=content)

        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO diary (title, content) VALUES (%s, %s)",
                (title, content),
            )
            entry_id = cur.lastrowid

        # Persist tag associations if any were selected
        if selected_tags:
            # Insert associations; ignore invalid values
            try:
                with conn.cursor() as cur:
                    for tid in selected_tags:
                        try:
                            tag_id = int(tid)
                        except (TypeError, ValueError):
                            continue
                        cur.execute(
                            "INSERT INTO diary_tags (diary_id, tag_id) VALUES (%s, %s)",
                            (entry_id, tag_id),
                        )
            except Exception:
                # Non-fatal: flash but continue
                flash('Warning: could not save some tag associations.', 'warning')

        flash('Entry created.', 'success')
        return redirect(url_for('home.preview'))

        # Load available tags for the form
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('SELECT id, name FROM tags ORDER BY name')
        tags = cur.fetchall()

    return render_template('diary/new.html', tags=tags)


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    """Edit an existing diary entry. Requires login."""
    if session.get('user_id') is None:
        return redirect(url_for('auth.login', next=request.path))

    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT id, title, content FROM diary WHERE id=%s", (id,))
        entry = cur.fetchone()

    if entry is None:
        flash('Entry not found.', 'error')
        return redirect(url_for('home.preview'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        # Collect tag ids submitted from the form (multiple-select)
        selected_tags = request.form.getlist('tags')

        if not title:
            flash('Title is required.', 'error')
            # Re-fetch tags for rendering
            with conn.cursor() as cur:
                cur.execute('SELECT id, name FROM tags ORDER BY name')
                tags = cur.fetchall()
                cur.execute('SELECT tag_id FROM diary_tags WHERE diary_id = %s', (id,))
                existing = [r['tag_id'] for r in cur.fetchall()]
            return render_template('diary/edit.html', entry=entry, tags=tags, existing_tag_ids=existing)

        with conn.cursor() as cur:
            cur.execute(
                "UPDATE diary SET title=%s, content=%s WHERE id=%s",
                (title, content, id),
            )

            # Update tag associations: remove existing and insert selected
            cur.execute('DELETE FROM diary_tags WHERE diary_id = %s', (id,))
            if selected_tags:
                for tid in selected_tags:
                    try:
                        tag_id = int(tid)
                    except (TypeError, ValueError):
                        continue
                    cur.execute(
                        "INSERT INTO diary_tags (diary_id, tag_id) VALUES (%s, %s)",
                        (id, tag_id),
                    )

        flash('Entry updated.', 'success')
        return redirect(url_for('home.preview'))

    # Load tags and existing tag ids for the form
    with conn.cursor() as cur:
        cur.execute('SELECT id, name FROM tags ORDER BY name')
        tags = cur.fetchall()
        cur.execute('SELECT tag_id FROM diary_tags WHERE diary_id = %s', (id,))
        existing = [r['tag_id'] for r in cur.fetchall()]

    return render_template('diary/edit.html', entry=entry, tags=tags, existing_tag_ids=existing)


@bp.route('/<int:id>')
def detail(id):
    """Show a single diary entry."""
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT id, title, content, created_at FROM diary WHERE id=%s", (id,))
        entry = cur.fetchone()

    if entry is None:
        flash('Entry not found.', 'error')
        return redirect(url_for('diary.index'))

    return render_template('diary/detail.html', entry=entry)


@bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    """Delete a diary entry and its tag associations."""
    if session.get('user_id') is None:
        return redirect(url_for('auth.login', next=request.path))

    conn = get_db()
    with conn.cursor() as cur:
        # Remove tag associations first
        cur.execute('DELETE FROM diary_tags WHERE diary_id = %s', (id,))
        # Delete the diary entry
        cur.execute('DELETE FROM diary WHERE id = %s', (id,))
        # Optionally check affected rows: not required

    flash('Entry deleted.', 'success')
    return redirect(url_for('home.preview'))