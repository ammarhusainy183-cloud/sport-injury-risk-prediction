import pytest
from app import create_app

@pytest.fixture
def app():
    app = create_app('development')
    app.config.update({
        'TESTING': True,
    })
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_health_endpoint(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'running' in data['message'].lower()


def test_landing_page_includes_profile_fields_for_registration(client):
    response = client.get('/')
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'athlete-registration-fields' in html
    assert 'id="reg-firstname"' in html
    assert 'id="reg-lastname"' in html
    assert 'id="reg-height"' in html
    assert 'id="reg-weight"' in html


def test_landing_page_registration_script_sends_profile_payload(client):
    response = client.get('/')
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'payload.profile = {' in html
    assert 'reg-firstname' in html
    assert 'reg-coach-email' in html
