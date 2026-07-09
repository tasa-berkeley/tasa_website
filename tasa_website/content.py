"""Load seed content from content.yaml.

content.yaml is a seed/sync source consumed by the Flask CLI (`seed-testimonials`,
`sync-officers`) — it is NOT the live site. Officers/families/testimonials pages read the
database. This module also provides the home/about image helpers (`site_image`/`photo_url`)
used by those static templates.
"""
import os

import yaml
from flask import current_app, url_for

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


def testimonials():
    """Testimonial entries from content.yaml (used by the `seed-testimonials` CLI)."""
    return _load().get('testimonials') or []


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
