"""No credentials, production data or real trading/network calls are used."""
import os
from unittest.mock import Mock
import django
from django.http import HttpResponse
from django.test import RequestFactory, override_settings
import pytest

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'geneticgrid.settings')
django.setup()
from core.public_access import PublicAccessMiddleware


@pytest.mark.parametrize('path', ['/api/proxy-config/', '/api/proxy-status/', '/api/proxy-test/',
    '/api/account/list/', '/api/account/session/', '/api/account/register/', '/api/account/login/',
    '/api/account/place-order/', '/api/strategies/', '/api/strategies/1/', '/admin/', '/future-api/'])
def test_public_control_plane_never_reaches_handler(path):
    handler = Mock(return_value=HttpResponse('should not run'))
    with override_settings(TIDE_PUBLIC_READ_ONLY=True):
        response = PublicAccessMiddleware(handler)(RequestFactory().get(path))
    assert response.status_code == 404
    handler.assert_not_called()


@pytest.mark.parametrize('method', ['post', 'put', 'patch', 'delete', 'options'])
def test_public_methods_never_reach_handler(method):
    handler = Mock()
    with override_settings(TIDE_PUBLIC_READ_ONLY=True):
        response = PublicAccessMiddleware(handler)(getattr(RequestFactory(), method)('/api/sources/'))
    assert response.status_code == 405
    handler.assert_not_called()


@pytest.mark.parametrize('path', ['/', '/market/', '/api/sources/', '/api/ticker/',
    '/api/candlesticks/', '/static/dist/assets/app.js'])
@pytest.mark.parametrize('method', ['get', 'head'])
def test_public_market_passes(path, method):
    handler = Mock(return_value=HttpResponse('market'))
    with override_settings(TIDE_PUBLIC_READ_ONLY=True):
        response = PublicAccessMiddleware(handler)(getattr(RequestFactory(), method)(path))
    assert response.status_code == 200
    assert response['X-Tide-Mode'] == 'public-market-only'
    handler.assert_called_once()


@pytest.mark.parametrize('value', ['0', '-1', '1000000', 'abc'])
def test_limit_rejected_before_work(value):
    handler = Mock()
    with override_settings(TIDE_PUBLIC_READ_ONLY=True):
        response = PublicAccessMiddleware(handler)(RequestFactory().get('/api/candlesticks/', {'limit': value}))
    assert response.status_code == 400
    handler.assert_not_called()


def test_private_mode_preserved():
    handler = Mock(return_value=HttpResponse('private'))
    with override_settings(TIDE_PUBLIC_READ_ONLY=False):
        assert PublicAccessMiddleware(handler)(RequestFactory().get('/admin/')).status_code == 200


def test_full_stack_public_index_and_control_plane():
    from django.test import Client
    with override_settings(TIDE_PUBLIC_READ_ONLY=True, ALLOWED_HOSTS=['testserver']):
        client = Client()
        response = client.get('/')
        assert response.status_code == 200
        assert b'name="tide-public-read-only" content="true"' in response.content
        assert client.get('/admin/login/').status_code == 404
        assert client.get('/api/account/list/').status_code == 404
        assert client.post('/api/proxy-config/', '{}', content_type='application/json').status_code == 405


def test_proxy_https_configuration():
    import subprocess
    import sys
    env = {**os.environ, 'TIDE_HTTPS_PROXY': 'true', 'ALLOWED_HOSTS': 'tide.sadd.ing,localhost',
           'DJANGO_SECRET_KEY': 'test-only-not-deployed', 'DJANGO_DEBUG': 'false'}
    result = subprocess.run([sys.executable, '-c',
        'from geneticgrid import settings as s; '
        'assert s.SESSION_COOKIE_SECURE and s.CSRF_COOKIE_SECURE; '
        'assert s.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https"); '
        'assert s.CSRF_TRUSTED_ORIGINS == ["https://tide.sadd.ing"]'],
        env=env, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
