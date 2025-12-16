



from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from diary.db import get_db
import pymysql

bp = Blueprint('tags', __name__, url_prefix='/tags')


@bp.route('/')
def index():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT t.id, t.name, COUNT(dt.diary_id) AS usage_count "
            "FROM tags t LEFT JOIN diary_tags dt ON dt.tag_id = t.id "
            "GROUP BY t.id ORDER BY t.name"
        )
        tags = cur.fetchall()

    return render_template('tags/index.html', tags=tags)


@bp.route('/new', methods=['GET', 'POST'])
def new():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Tag name is required.')
            return render_template('tags/new.html')

        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute('INSERT INTO tags (name) VALUES (%s)', (name,))
        except pymysql.err.IntegrityError:
            flash('A tag with that name already exists.')
            return render_template('tags/new.html')

        flash('Tag created.')
        return redirect(url_for('tags.index'))

    return render_template('tags/new.html')


@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('SELECT id, name FROM tags WHERE id = %s', (id,))
        tag = cur.fetchone()

    if tag is None:
        abort(404)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Tag name is required.')
            return render_template('tags/edit.html', tag=tag)

        try:
            with conn.cursor() as cur:
                cur.execute('UPDATE tags SET name = %s WHERE id = %s', (name, id))
        except pymysql.err.IntegrityError:
            flash('A tag with that name already exists.')
            return render_template('tags/edit.html', tag=tag)

        flash('Tag updated.')
        return redirect(url_for('tags.index'))

    return render_template('tags/edit.html', tag=tag)


@bp.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    conn = get_db()
    with conn.cursor() as cur:
        # Remove associations first to be explicit, then remove tag
        cur.execute('DELETE FROM diary_tags WHERE tag_id = %s', (id,))
        cur.execute('DELETE FROM tags WHERE id = %s', (id,))

    flash('Tag deleted.')
    return redirect(url_for('tags.index'))


@bp.route('/create', methods=['POST'])
def create():
    """Create a tag via AJAX/JSON. Accepts form or JSON `name` and returns JSON.

    Returns 201 with JSON {id, name} on success, 400 for bad input, 409 for duplicate.
    """
    data = request.get_json(silent=True)
    name = None
    if data and 'name' in data:
        name = data.get('name', '').strip()
    else:
        # fallback to form-encoded
        name = request.form.get('name', '').strip()

    if not name:
        return jsonify({'error': 'Tag name is required.'}), 400

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute('INSERT INTO tags (name) VALUES (%s)', (name,))
            tag_id = cur.lastrowid
    except pymysql.err.IntegrityError:
        return jsonify({'error': 'Tag already exists.'}), 409
    except Exception:
        return jsonify({'error': 'Could not create tag.'}), 500

    return jsonify({'id': tag_id, 'name': name}), 201