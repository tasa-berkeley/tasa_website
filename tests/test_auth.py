def test_admin_requires_login(client):
    response = client.get('/admin/')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_bad_credentials_rejected(client):
    response = client.post('/login', data={'username': 'admin', 'password': 'wrong'})
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data
    assert client.get('/admin/').status_code == 302


def test_good_credentials_reach_dashboard(client):
    response = client.post('/login', data={'username': 'admin', 'password': 'testpass'})
    assert response.status_code == 302
    assert client.get('/admin/').status_code == 200


def test_logout(logged_in):
    logged_in.get('/logout')
    assert logged_in.get('/admin/').status_code == 302


def test_login_next_must_be_relative(client):
    response = client.post('/login?next=https://evil.example.com',
                           data={'username': 'admin', 'password': 'testpass'})
    assert response.headers['Location'] == '/admin/'
