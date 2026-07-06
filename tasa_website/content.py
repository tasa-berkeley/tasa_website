"""Load site content from content.yaml — the single source of truth for the site.

Webmasters edit content.yaml (no database). This module parses it (re-reading only when
the file changes) and exposes the data to the views and templates.
"""
import os

import yaml
from flask import current_app, url_for

# Officer sections render in this fixed order; 'Interns' always shows (for the
# "apply to be an intern" placeholder) even when its list is empty.
SECTION_ORDER = [
    ('Executives', 'executives'),
    ('Officers', 'officers'),
    ('Interns', 'interns'),
    ('Senior Advisors', 'senior_advisors'),
]

_cache = {'mtime': None, 'data': None}


def _content_path():
    return os.path.join(current_app.root_path, 'content.yaml')


def _load():
    """Parse content.yaml, re-reading only when the file's mtime changes."""
    path = _content_path()
    mtime = os.path.getmtime(path)
    if _cache['mtime'] != mtime:
        with open(path, encoding='utf-8') as fh:
            _cache['data'] = yaml.safe_load(fh) or {}
        _cache['mtime'] = mtime
    return _cache['data']


def _with_ids(entries):
    """Attach a stable per-list id so the template's expand/modal can key on it."""
    out = []
    for i, entry in enumerate(entries or []):
        item = dict(entry)
        item['id'] = i
        out.append(item)
    return out


def officer_sections():
    """Return [(section label, [officers])]; empty sections dropped except Interns."""
    officers = _load().get('officers') or {}
    result = []
    for label, key in SECTION_ORDER:
        people = _with_ids(officers.get(key))
        # ids must be unique across the whole page, so offset by what's already emitted
        offset = sum(len(sec) for _, sec in result)
        for person in people:
            person['id'] += offset
        if people or key == 'interns':
            result.append((label, people))
    return result


def families():
    return _with_ids(_load().get('families'))


def testimonials():
    return _with_ids(_load().get('testimonials'))


def photo_url(subfolder, filename):
    """URL for a photo in static/images/<subfolder>/, or None if the file is missing."""
    if not filename:
        return None
    rel = 'images/' + subfolder + '/' + filename
    if os.path.exists(os.path.join(current_app.static_folder, *rel.split('/'))):
        return url_for('static', filename=rel)
    return None


def site_image(filename):
    """URL for a hand-placed photo in static/images/site/, or None until one is added."""
    return photo_url('site', filename)
