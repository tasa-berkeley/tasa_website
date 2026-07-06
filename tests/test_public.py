import pytest

PUBLIC_ROUTES = ['/', '/about', '/officers', '/families', '/testimonials', '/join']

REMOVED_ROUTES = [
    '/events', '/donate', '/contact', '/scrapbook/fa19',
    '/checkin', '/checkin_successful', '/rolling', '/members/download', '/files',
]


@pytest.mark.parametrize('path', PUBLIC_ROUTES)
def test_public_routes_ok(client, path):
    response = client.get(path)
    assert response.status_code == 200


@pytest.mark.parametrize('path', REMOVED_ROUTES)
def test_removed_routes_gone(client, path):
    assert client.get(path).status_code == 404
