import io

import pytest
from PIL import Image
from werkzeug.security import generate_password_hash

from tasa_website import create_app
from tasa_website.extensions import db


@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite://',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test',
        'ADMIN_USERNAME': 'admin',
        'ADMIN_PASSWORD_HASH': generate_password_hash('testpass'),
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def logged_in(client):
    client.post('/login', data={'username': 'admin', 'password': 'testpass'})
    return client


def make_test_image():
    """A tiny in-memory JPEG suitable for upload fields."""
    buf = io.BytesIO()
    Image.new('RGB', (8, 8), 'blue').save(buf, format='JPEG')
    buf.seek(0)
    return buf, 'test.jpg'
