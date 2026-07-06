from tasa_website import create_app
from tasa_website import content


def _ctx():
    return create_app({'TESTING': True}).app_context()


def test_officer_sections_order_and_interns_always_present():
    with _ctx():
        sections = content.officer_sections()
    labels = [name for name, _ in sections]
    # Interns always renders (for the recruitment placeholder); order is fixed.
    assert labels == ['Executives', 'Officers', 'Interns', 'Senior Advisors']


def test_officer_ids_unique_across_sections():
    with _ctx():
        sections = content.officer_sections()
    ids = [o['id'] for _, people in sections for o in people]
    assert len(ids) == len(set(ids))


def test_families_and_testimonials_load():
    with _ctx():
        fams = content.families()
        tests = content.testimonials()
    assert all('name' in f and 'id' in f for f in fams)
    assert all('question' in t and 'response' in t for t in tests)


def test_photo_url_missing_returns_none():
    with _ctx():
        assert content.photo_url('officers', 'definitely-not-a-real-file.jpg') is None
        assert content.photo_url('officers', None) is None
