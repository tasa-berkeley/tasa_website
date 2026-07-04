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

    # appears on the public page grouped under Executive Board
    page = logged_in.get('/officers')
    assert b'Test Officer' in page.data and b'Executive Board' in page.data

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
