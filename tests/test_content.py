from tasa_website import create_app
from tasa_website import content


def _ctx():
    return create_app({'TESTING': True}).app_context()


def test_testimonials_load():
    with _ctx():
        tests = content.testimonials()
    # content.yaml testimonials feed the `seed-testimonials` CLI.
    assert all('question' in t and 'response' in t for t in tests)


def test_photo_url_missing_returns_none():
    with _ctx():
        assert content.photo_url('officers', 'definitely-not-a-real-file.jpg') is None
        assert content.photo_url('officers', None) is None
