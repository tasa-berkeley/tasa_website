"""Positions, officer grouping, and the image upload pipeline."""
import os
import posixpath
import random
import string

from flask import current_app, url_for
from PIL import Image

from .majors import major_category

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


def base_role(index):
    """The role *family* for a position index — interns fold into their base role.

    'Webmaster Intern' and 'Webmaster' both map to 'Webmaster', so the /alumni Position lineage
    treats them as one succession. Non-intern titles map to themselves.
    """
    return position_title(index).removesuffix(' Intern')


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


# --- Cabinet alumni (lineage features) ----------------------------------

# Seasons in chronological order within a calendar year, so Fall 2023 precedes Spring 2024.
SEASONS = ['Spring', 'Summer', 'Fall']
SEASON_RANK = {s: i for i, s in enumerate(SEASONS)}


def semester_sort_key(season, year):
    """A chronological (year, season) sort key: Spring < Summer < Fall within a year."""
    return (int(year or 0), SEASON_RANK.get(season, 0))


def semester_ordinal(season, year):
    """A single sortable integer for a semester (for the client), e.g. Fall 2023 -> 20232."""
    return int(year or 0) * 10 + SEASON_RANK.get(season, 0)


def semester_label(season, year):
    """Human label for a semester, e.g. 'Fall 2023'."""
    return f'{season} {year}'.strip() if (season or year) else ''


def normalize_instagram(raw):
    """Reduce free-form Instagram input to a bare handle (no '@', no URL), or None."""
    if not raw or not raw.strip():
        return None
    handle = raw.strip()
    if '://' in handle:
        handle = handle.split('://', 1)[1]
    handle = handle.removeprefix('www.')
    if handle.lower().startswith('instagram.com/'):
        handle = handle[len('instagram.com/'):]
    handle = handle.lstrip('@').strip('/').split('/')[0].split('?')[0]
    return handle or None


def instagram_url(handle):
    """Public Instagram URL for a stored handle."""
    return f'https://www.instagram.com/{handle}' if handle else None


def normalize_linkedin(raw):
    """Reduce free-form LinkedIn input to a canonical profile URL, or None.

    Accepts a full URL, a 'linkedin.com/...' string, an 'in/<slug>' path, or a bare vanity
    slug. Bare slugs become 'https://www.linkedin.com/in/<slug>'; an explicit linkedin.com
    URL/path is preserved (so company/school pages keep working).
    """
    if not raw or not raw.strip():
        return None
    val = raw.strip()
    low = val.lower()
    if low.startswith('http://') or low.startswith('https://'):
        return 'https://' + val.split('://', 1)[1]
    if low.startswith('www.linkedin.com/') or low.startswith('linkedin.com/'):
        return 'https://' + val.removeprefix('www.')
    slug = val.strip('/')
    if slug.lower().startswith('in/'):
        slug = slug[3:].strip('/')
    return f'https://www.linkedin.com/in/{slug}' if slug else None


def cabinet_descendant_ids(member):
    """All ids in `member`'s subtree (its littles, recursively). Used to block big/little cycles."""
    seen = set()
    stack = list(member.littles)
    while stack:
        child = stack.pop()
        if child.id in seen:
            continue
        seen.add(child.id)
        stack.extend(child.littles)
    return seen


def cabinet_initials(name):
    """Up to two initials for a name, for photo-less graph nodes."""
    parts = [p for p in (name or '').split() if p]
    if not parts:
        return '?'
    if len(parts) == 1:
        return parts[0][0].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def cabinet_member_terms(m):
    """A member's position terms as sortable dicts, ordered chronologically by semester.

    `value` is the role *family* (interns folded in) so the Position lineage chains e.g. every
    Webmaster together; `label` keeps the specific title held (e.g. 'Webmaster Intern') for the modal.
    """
    terms = sorted(m.terms, key=lambda t: semester_sort_key(t.season, t.year))
    return [
        {
            'value': base_role(t.position),                # group key = role family (interns folded)
            'label': position_title(t.position),           # specific title held (shown in the modal)
            'season': t.season,
            'year': t.year,
            'semester': semester_label(t.season, t.year),
            'sortKey': semester_ordinal(t.season, t.year),  # chronological order within the role
        }
        for t in terms
    ]


def cabinet_member_dict(m):
    """Serialize a CabinetMember for the /alumni graph JSON.

    Exposes a generic 'feature' shape the client's lineage engine reads without knowing about any
    specific feature: `relations` (person->person links), `attributes` (single values), and
    `sequences` (multi-valued, time-ordered lists). Top-level fields are kept for filters + the modal.
    """
    return {
        'id': m.id,
        'name': m.name,
        'grad_year': m.grad_year,
        'role': m.role or '',
        'major': m.major or '',
        'instagram': m.instagram or '',
        'instagram_url': instagram_url(m.instagram) or '',
        'email': m.email or '',
        'linkedin': m.linkedin or '',
        'bio': m.bio or '',
        'image': static_image(m.image_url) or '',
        'big_id': m.big_id,
        'initials': cabinet_initials(m.name),
        # --- generic features consumed by the lineage engine ---
        'relations': {'big': m.big_id},
        'attributes': {
            'major': m.major or '',
            'majorField': major_category(m.major),
            'classYear': m.grad_year,
            'internClass': semester_label(m.intern_season, m.intern_year) if m.intern_year else '',
            'internClassOrd': (semester_ordinal(m.intern_season, m.intern_year) if m.intern_year else None),
        },
        'sequences': {'position': cabinet_member_terms(m)},
    }
