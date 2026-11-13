"""Production configuration checks, without databases or exchange credentials."""
import os
import subprocess
import sys


def load_settings(**overrides):
    env = {**os.environ, 'DATABASE_URL': 'postgres://test:test@localhost/test',
           'REALTIME_INGESTION_AUTO_START': 'false'}
    env.pop('DJANGO_DEBUG', None)
    env.pop('DJANGO_SECRET_KEY', None)
    env.update(overrides)
    return subprocess.run(
        [sys.executable, '-c', 'from geneticgrid.settings import DEBUG; print(DEBUG)'],
        env=env, text=True, capture_output=True, check=False,
    )


def test_production_requires_secret():
    result = load_settings()
    assert result.returncode != 0
    assert 'DJANGO_SECRET_KEY' in result.stderr


def test_production_debug_off_with_secret():
    result = load_settings(DJANGO_SECRET_KEY='test-only-random-secret-not-for-deployment')
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'False'


def test_explicit_development_mode():
    result = load_settings(DJANGO_DEBUG='true')
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'True'
