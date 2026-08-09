from tasa_website import helpers
from tasa_website.extensions import db
from tasa_website.models import CabinetMember, CabinetTerm


def _add_member(client, **fields):
    """POST the new-member form with sensible blanks, overridden by **fields."""
    data = {'name': 'X', 'grad_year': '', 'role': '', 'major': '', 'instagram': '',
            'email': '', 'linkedin': '', 'bio': '', 'big_id': '0'}
    data.update(fields)
    return client.post('/admin/alumni/new', data=data,
                       content_type='multipart/form-data', follow_redirects=True)


def _by_name(name):
    return db.session.scalars(db.select(CabinetMember).where(CabinetMember.name == name)).one()


def test_cabinet_crud_and_relationship(app, logged_in):
    # A big (top of a lineage); Instagram/LinkedIn get normalized on save.
    response = _add_member(logged_in, name='Big Al', grad_year='2018', instagram='@bigal', linkedin='bigal')
    assert b'Added Big Al' in response.data
    big = _by_name('Big Al')
    assert big.instagram == 'bigal'
    assert big.linkedin == 'https://www.linkedin.com/in/bigal'
    assert big.grad_year == 2018

    # A little pointing at the big
    response = _add_member(logged_in, name='Little Lou', grad_year='2021', big_id=str(big.id))
    assert b'Added Little Lou' in response.data
    little = _by_name('Little Lou')
    assert little.big_id == big.id
    assert [m.name for m in big.littles] == ['Little Lou']

    # Public page renders the member, the inlined graph data, and the graph container.
    page = logged_in.get('/alumni')
    assert page.status_code == 200
    assert b'Big Al' in page.data and b'CABINET_DATA' in page.data and b'cabinet-cy' in page.data


def test_delete_reparents_littles(app, logged_in):
    _add_member(logged_in, name='Root')
    root = _by_name('Root')
    _add_member(logged_in, name='Child', big_id=str(root.id))
    child_id = _by_name('Child').id

    response = logged_in.post(f'/admin/alumni/{root.id}/delete', follow_redirects=True)
    assert b'Deleted Root' in response.data
    # The little survives and becomes a root (big cleared) — never cascade-deleted.
    child = db.session.get(CabinetMember, child_id)
    assert child is not None and child.big_id is None


def test_cycle_prevention(app, logged_in):
    _add_member(logged_in, name='A')
    a = _by_name('A')
    _add_member(logged_in, name='B', big_id=str(a.id))
    b = _by_name('B')

    # Making A's big be B (B is A's descendant) would create a cycle -> rejected, A unchanged.
    response = logged_in.post(f'/admin/alumni/{a.id}/edit', data={
        'name': 'A', 'grad_year': '', 'role': '', 'major': '', 'instagram': '',
        'email': '', 'linkedin': '', 'bio': '', 'big_id': str(b.id),
    }, content_type='multipart/form-data', follow_redirects=True)
    assert b'cannot be their own big' in response.data
    assert db.session.get(CabinetMember, a.id).big_id is None


def test_alumni_admin_requires_login(client):
    assert client.get('/admin/alumni').status_code == 302
    assert client.post('/admin/alumni/new', data={}).status_code == 302


def test_normalize_instagram():
    assert helpers.normalize_instagram('  @Foo_Bar ') == 'Foo_Bar'
    assert helpers.normalize_instagram('https://instagram.com/johndoe/') == 'johndoe'
    assert helpers.normalize_instagram('') is None
    assert helpers.normalize_instagram(None) is None


def test_normalize_linkedin():
    assert helpers.normalize_linkedin('jane') == 'https://www.linkedin.com/in/jane'
    assert helpers.normalize_linkedin('in/jane-d') == 'https://www.linkedin.com/in/jane-d'
    assert helpers.normalize_linkedin('https://www.linkedin.com/in/x?trk=1') == 'https://www.linkedin.com/in/x?trk=1'
    assert helpers.normalize_linkedin('') is None


def test_semester_ordering_helpers():
    # Fall precedes the next Spring; Spring precedes Fall within the same year.
    assert helpers.semester_ordinal('Fall', 2023) < helpers.semester_ordinal('Spring', 2024)
    assert helpers.semester_sort_key('Spring', 2024) < helpers.semester_sort_key('Fall', 2024)
    assert helpers.semester_label('Fall', 2023) == 'Fall 2023'


def _member_form_data(**over):
    data = {'name': 'X', 'grad_year': '', 'role': '', 'major': '', 'instagram': '',
            'email': '', 'linkedin': '', 'bio': '', 'big_id': '0'}
    data.update(over)
    return data


def test_member_terms_crud_and_chronological_serialization(app, logged_in):
    # Create with two terms submitted out of chronological order (each field is a list -> repeated input).
    data = _member_form_data(name='Termy', major='EECS')
    data['term_position[]'] = ['1', '12']     # 1 = Internal Vice President, 12 = Treasurer Intern
    data['term_season[]'] = ['Spring', 'Fall']
    data['term_year[]'] = ['2024', '2023']
    response = logged_in.post('/admin/alumni/new', data=data,
                              content_type='multipart/form-data', follow_redirects=True)
    assert b'Added Termy' in response.data
    m = _by_name('Termy')
    assert len(m.terms) == 2

    # Serialized position sequence is chronological: Fall 2023 (Treasurer Intern) then Spring 2024 (IVP).
    seq = helpers.cabinet_member_dict(m)['sequences']['position']
    assert [t['semester'] for t in seq] == ['Fall 2023', 'Spring 2024']
    assert seq[0]['sortKey'] < seq[1]['sortKey']

    # Edit down to a single term; the dropped one is deleted (cascade delete-orphan).
    edit = _member_form_data(name='Termy', major='EECS')
    edit['term_position[]'] = ['1']
    edit['term_season[]'] = ['Spring']
    edit['term_year[]'] = ['2024']
    response = logged_in.post(f'/admin/alumni/{m.id}/edit', data=edit,
                              content_type='multipart/form-data', follow_redirects=True)
    assert b'Updated Termy' in response.data
    m = _by_name('Termy')
    assert len(m.terms) == 1 and m.terms[0].position == 1
    assert len(db.session.scalars(db.select(CabinetTerm)).all()) == 1

    # Deleting the member cascades its terms.
    logged_in.post(f'/admin/alumni/{m.id}/delete', follow_redirects=True)
    assert db.session.scalars(db.select(CabinetTerm)).all() == []


def test_base_role_folds_interns():
    from tasa_website.helpers import POSITIONS, base_role
    assert base_role(POSITIONS.index('Webmaster')) == 'Webmaster'
    assert base_role(POSITIONS.index('Webmaster Intern')) == 'Webmaster'
    assert base_role(POSITIONS.index('Treasurer Intern')) == 'Treasurer'


def test_major_category_helper():
    from tasa_website.majors import is_known_major, major_category
    assert major_category('Data Science') == 'Computing & Data Science'
    assert major_category('Applied Mathematics') == 'Mathematical & Physical Sciences'
    assert major_category('Not A Real Major') == ''
    assert is_known_major('Economics') and not is_known_major('DS')


def test_position_folding_intern_class_and_major_field(app, logged_in):
    data = _member_form_data(name='Foldy', major='Data Science')
    data['intern_season'] = 'Fall'
    data['intern_year'] = '2022'
    data['term_position[]'] = ['13', '4']    # Webmaster Intern, then Webmaster
    data['term_season[]'] = ['Fall', 'Spring']
    data['term_year[]'] = ['2022', '2023']
    response = logged_in.post('/admin/alumni/new', data=data,
                              content_type='multipart/form-data', follow_redirects=True)
    assert b'Added Foldy' in response.data
    m = _by_name('Foldy')
    assert m.intern_season == 'Fall' and m.intern_year == 2022

    d = helpers.cabinet_member_dict(m)
    # Both terms collapse into one 'Webmaster' role group, but keep their specific titles for the modal.
    assert {t['value'] for t in d['sequences']['position']} == {'Webmaster'}
    assert [t['label'] for t in d['sequences']['position']] == ['Webmaster Intern', 'Webmaster']
    assert d['attributes']['internClass'] == 'Fall 2022'
    assert d['attributes']['majorField'] == 'Computing & Data Science'
    assert d['attributes']['major'] == 'Data Science'


def test_blank_term_rows_are_skipped(app, logged_in):
    data = _member_form_data(name='Blanky')
    data['term_position[]'] = ['', '3']       # first row is blank and must be ignored
    data['term_season[]'] = ['Fall', 'Fall']
    data['term_year[]'] = ['', '2022']
    logged_in.post('/admin/alumni/new', data=data,
                   content_type='multipart/form-data', follow_redirects=True)
    m = _by_name('Blanky')
    assert len(m.terms) == 1 and m.terms[0].position == 3 and m.terms[0].year == 2022
