"""Positions, officer grouping, and the image upload pipeline."""
import os
import posixpath
import random
import string

from flask import current_app, url_for
from PIL import Image

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'gif', 'png'}

# The officers table stores position as an index into this list, so the list
# order is load-bearing: append new titles, never reorder existing ones.
POSITIONS = [
    'President',
    'Internal Vice President',
    'External Vice President',
    'Treasurer',
    'Webmaster',
    'Outreach',
    'Design',
    'Marketing',
    'Public Relations',
    'Family Head',
    'Historian',
    'Senior Advisor',
    'Treasurer Intern',
    'Webmaster Intern',
    'Outreach Intern',
    'Design Intern',
    'Marketing Intern',
    'Public Relations Intern',
    'Family Head Intern',
    'Historian Intern',
    # Appended (never reorder the above — stored position indices depend on it):
    'Social',
]

SECTION_ORDER = ['Executives', 'Officers', 'Interns', 'Senior Advisors']

IMAGE_MAXSIZE = (1024, 1024)


def position_title(index):
    if 0 <= index < len(POSITIONS):
        return POSITIONS[index]
    return 'Officer'


def position_section(index):
    """Map a position index to its section on the officers page."""
    if not 0 <= index < len(POSITIONS):
        return 'Officers'
    if index <= 2:  # President, Internal VP, External VP
        return 'Executives'
    title = POSITIONS[index]
    if title == 'Senior Advisor':
        return 'Senior Advisors'
    if title.endswith('Intern'):
        return 'Interns'
    return 'Officers'


def officer_sections(officers):
    """Bucket officers into ordered (section name, officers) pairs.

    Empty sections are dropped, except 'Interns' which always renders so the page
    can show the "apply to be an intern" recruitment placeholder.
    """
    buckets = {name: [] for name in SECTION_ORDER}
    for officer in officers:
        buckets[position_section(officer.position)].append(officer)
    for bucket in buckets.values():
        # Order by rank (position), then curated content.yaml order, then name. This keeps
        # same-position groups (e.g. Senior Advisors) in the order set in content.yaml.
        bucket.sort(key=lambda o: (o.position, o.display_order, o.name))
    return [(name, buckets[name]) for name in SECTION_ORDER if buckets[name] or name == 'Interns']


def static_image(image_url):
    """Turn a stored image path ('static/images/officers/X.jpg') into a servable URL."""
    if not image_url:
        return None
    return url_for('static', filename=image_url.removeprefix('static/'))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_random_filename(extension):
    name = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8))
    return name + '.' + extension


def create_file_paths(sub_root, file_name):
    # The stored URL must always use forward slashes, even on Windows dev machines
    file_url = posixpath.join(sub_root, file_name)
    file_path = os.path.join(current_app.root_path, *file_url.split('/'))
    return file_url, file_path


def save_image(file_storage, save_folder):
    """Resize an uploaded image, save it as a JPEG under save_folder, return its stored URL."""
    if not allowed_file(file_storage.filename):
        raise ValueError('Not a supported image format. Must be jpg, jpeg, png, or gif.')
    file_url, file_path = create_file_paths(save_folder, generate_random_filename('jpg'))
    img = Image.open(file_storage)
    img.thumbnail(IMAGE_MAXSIZE)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img.save(file_path, format='JPEG', quality=95, optimize=True, progressive=True)
    return file_url


def delete_image(image_url):
    """Best-effort removal of an uploaded image file when its row is deleted or replaced."""
    if not image_url or not image_url.startswith('static/images/'):
        return
    path = os.path.join(current_app.root_path, *image_url.split('/'))
    try:
        os.remove(path)
    except OSError:
        pass
