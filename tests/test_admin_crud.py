from tasa_website.extensions import db
from tasa_website.models import Family, Officer, Testimonial

from .conftest import make_test_image


def test_officer_crud_round_trip(app, logged_in):
    # create (image required)
    response = logged_in.post('/admin/officers/new', data={
        'name': 'Test Officer', 'position': '0', 'major': 'EECS', 'year': '2027',
        'quote': '', 'description': '', 'image': make_test_image(),
    }, content_type='multipart/form-data', follow_redirects=True)
    assert b'Added officer Test Officer' in response.data

    officer = db.session.scalars(db.select(Officer)).one()
    assert officer.image_url.startswith('static/images/officers/')
    assert '\\' not in officer.image_url  # posix-style URL even on Windows

    # appears on the public page grouped under Executives
    page = logged_in.get('/officers')
    assert b'Test Officer' in page.data and b'Executives' in page.data

    # edit without replacing the image
    response = logged_in.post(f'/admin/officers/{officer.id}/edit', data={
        'name': 'Renamed Officer', 'position': '4', 'major': 'EECS', 'year': '2027',
        'quote': '', 'description': '',
    }, content_type='multipart/form-data', follow_redirects=True)
    assert b'Updated officer Renamed Officer' in response.data
    assert db.session.get(Officer, officer.id).position == 4

    # delete
    response = logged_in.post(f'/admin/officers/{officer.id}/delete', follow_redirects=True)
    assert b'Deleted officer' in response.data
    assert db.session.scalars(db.select(Officer)).all() == []


def test_officer_create_requires_image(logged_in):
    response = logged_in.post('/admin/officers/new', data={
        'name': 'No Photo', 'position': '0', 'major': 'EECS', 'year': '2027',
    }, content_type='multipart/form-data')
    assert b'A photo is required' in response.data
    assert db.session.scalars(db.select(Officer)).all() == []


def test_family_crud_round_trip(app, logged_in):
    response = logged_in.post('/admin/families/new', data={
        'family_name': 'Boba', 'family_head1': 'Alice', 'family_head2': 'Bob',
        'family_head_intern': '', 'description': 'The boba family.',
        'image': make_test_image(),
    }, content_type='multipart/form-data', follow_redirects=True)
    assert b'Added family Boba' in response.data

    family = db.session.scalars(db.select(Family)).one()
    assert family.heads() == 'Alice & Bob'

    page = logged_in.get('/families')
    assert b'Boba' in page.data

    response = logged_in.post(f'/admin/families/{family.id}/delete', follow_redirects=True)
    assert b'Deleted family' in response.data
    assert db.session.scalars(db.select(Family)).all() == []


def test_testimonial_crud_round_trip(app, logged_in):
    # image is optional for testimonials
    response = logged_in.post('/admin/testimonials/new', data={
        'name': 'Happy Member', 'position': 'Historian Officer, President',
        'question': 'Why TASA?', 'response': 'Because it feels like family.',
    }, content_type='multipart/form-data', follow_redirects=True)
    assert b'Added testimonial from Happy Member' in response.data

    testimonial = db.session.scalars(db.select(Testimonial)).one()
    assert testimonial.image_url is None

    page = logged_in.get('/testimonials')
    assert b'Happy Member' in page.data and b'Why TASA?' in page.data

    response = logged_in.post(f'/admin/testimonials/{testimonial.id}/delete', follow_redirects=True)
    assert b'Deleted testimonial' in response.data
    assert db.session.scalars(db.select(Testimonial)).all() == []


def test_admin_crud_requires_login(client):
    assert client.get('/admin/officers').status_code == 302
    assert client.post('/admin/officers/new', data={}).status_code == 302


def test_officers_sort_by_year_desc(app, logged_in):
    for name, year in [('Aaa Sort', '2025'), ('Bbb Sort', '2027'), ('Ccc Sort', '2026')]:
        logged_in.post('/admin/officers/new', data={
            'name': name, 'position': '0', 'major': 'EECS', 'year': year,
            'quote': '', 'description': '', 'image': make_test_image(),
        }, content_type='multipart/form-data', follow_redirects=True)  # follow to consume flash messages
    html = logged_in.get('/admin/officers?sort=year&dir=desc').get_data(as_text=True)
    assert html.index('Bbb Sort') < html.index('Ccc Sort') < html.index('Aaa Sort')


def test_intern_lands_in_interns_section(app, logged_in):
    from tasa_website.helpers import POSITIONS
    intern_index = POSITIONS.index('Webmaster Intern')
    logged_in.post('/admin/officers/new', data={
        'name': 'Intern Ivy', 'position': str(intern_index), 'major': 'EECS', 'year': 'Freshman',
        'quote': '', 'description': 'Excited to join!', 'image': make_test_image(),
    }, content_type='multipart/form-data', follow_redirects=True)
    page = logged_in.get('/officers').get_data(as_text=True)
    assert 'Intern Ivy' in page
    # the Interns bucket is now non-empty, so the recruitment placeholder is gone
    assert 'Apply to be a Fall 2026 Intern' not in page
