from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from diary.db import get_db
import pymysql

bp = Blueprint('tags', __name__, url_prefix='/tags')


@bp.route('/')
def index():
    conn = get_db()
    with conn.cursor() as cur:
        # Fetch tags with parent_id and usage counts (direct uses only)
        cur.execute(
            "SELECT t.id, t.name, t.parent_id, COUNT(dt.diary_id) AS usage_count "
            "FROM tags t LEFT JOIN diary_tags dt ON dt.tag_id = t.id "
            "GROUP BY t.id ORDER BY t.name"
        )
        rows = cur.fetchall()

    # Build maps for tier computation
    parent = {r['id']: r.get('parent_id') for r in rows}
    usage = {r['id']: r['usage_count'] for r in rows}
    name = {r['id']: r['name'] for r in rows}

    # Compute tier (depth) for each tag with memoization and cycle protection
    tiers = {}
    def compute_tier(tag_id):
        if tag_id in tiers:
            return tiers[tag_id]
        seen = set()
        depth = 0
        cur = tag_id
        while True:
            pid = parent.get(cur)
            if not pid:
                tiers[tag_id] = depth
                return depth
            if pid in seen:
                # cycle detected, treat as root
                tiers[tag_id] = 0
                return 0
            seen.add(pid)
            depth += 1
            if pid in tiers:
                tiers[tag_id] = depth + tiers[pid]
                return tiers[tag_id]
            cur = pid

    max_tier = 0
    groups = {}
    for r in rows:
        tid = r['id']
        t = compute_tier(tid)
        max_tier = max(max_tier, t)
        groups.setdefault(t, []).append({'id': tid, 'name': name[tid], 'parent_id': parent.get(tid), 'usage_count': usage.get(tid, 0)})

    return render_template('tags/index.html', tag_groups=groups, max_tier=max_tier)

@bp.route('/trees')
def trees():
    conn = get_db()
    with conn.cursor() as cur:
        # Fetch tags with parent_id and usage counts (direct uses only)
        cur.execute(
            "SELECT t.id, t.name, t.parent_id, COUNT(dt.diary_id) AS usage_count "
            "FROM tags t LEFT JOIN diary_tags dt ON dt.tag_id = t.id "
            "GROUP BY t.id ORDER BY t.name"
        )
        rows = cur.fetchall()

    # Build nodes and tree
    nodes = {r['id']: {'id': r['id'], 'name': r['name'], 'parent_id': r.get('parent_id'), 'usage_count': r['usage_count'], 'children': []} for r in rows}
    roots = []
    for n in nodes.values():
        pid = n.get('parent_id')
        if pid and pid in nodes:
            nodes[pid]['children'].append(n)
        else:
            roots.append(n)

    return render_template('tags/trees.html', tag_tree=roots)


@bp.route('/new', methods=['GET', 'POST'])
def new():
    conn = get_db()
    # Fetch existing tags for parent selection
    with conn.cursor() as cur:
        cur.execute('SELECT id, name FROM tags ORDER BY name')
        all_tags = cur.fetchall()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        parent_raw = request.form.get('parent_id', '').strip()
        parent_id = None
        if parent_raw:
            try:
                parent_id = int(parent_raw)
            except (TypeError, ValueError):
                parent_id = None

        if not name:
            flash('Tag name is required.')
            return render_template('tags/new.html', tags=all_tags)

        try:
            with conn.cursor() as cur:
                cur.execute('INSERT INTO tags (name, parent_id) VALUES (%s, %s)', (name, parent_id))
        except pymysql.err.IntegrityError:
            flash('A tag with that name already exists.')
            return render_template('tags/new.html', tags=all_tags)

        flash('Tag created.')
        return redirect(url_for('tags.new'))

    return render_template('tags/new.html', tags=all_tags)


@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('SELECT id, name, parent_id FROM tags WHERE id = %s', (id,))
        tag = cur.fetchone()

    if tag is None:
        abort(404)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        parent_raw = request.form.get('parent_id', '').strip()
        parent_id = None
        if parent_raw:
            try:
                parent_id = int(parent_raw)
            except (TypeError, ValueError):
                parent_id = None

        if not name:
            flash('Tag name is required.')
            # Re-fetch tags for parent select
            with conn.cursor() as cur:
                cur.execute('SELECT id, name FROM tags WHERE id != %s ORDER BY name', (id,))
                all_tags = cur.fetchall()
            return render_template('tags/edit.html', tag=tag, tags=all_tags)

        try:
            with conn.cursor() as cur:
                cur.execute('UPDATE tags SET name = %s, parent_id = %s WHERE id = %s', (name, parent_id, id))
        except pymysql.err.IntegrityError:
            flash('A tag with that name already exists.')
            with conn.cursor() as cur:
                cur.execute('SELECT id, name FROM tags WHERE id != %s ORDER BY name', (id,))
                all_tags = cur.fetchall()
            return render_template('tags/edit.html', tag=tag, tags=all_tags)

        flash('Tag updated.')
        return redirect(url_for('tags.index'))

    # GET: fetch tags for parent select (exclude self)
    with conn.cursor() as cur:
        cur.execute('SELECT id, name FROM tags WHERE id != %s ORDER BY name', (id,))
        all_tags = cur.fetchall()

    return render_template('tags/edit.html', tag=tag, tags=all_tags)


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