#!/usr/bin/env bash
# Isolated CI validation, never points at production volumes or credentials.
set -euo pipefail
cd "$(dirname "$0")/.."
: "${GENETICGRID_IMAGE:?Build and set GENETICGRID_IMAGE first}"
export DJANGO_SECRET_KEY="$(openssl rand -hex 32)"
export POSTGRES_PASSWORD="$(openssl rand -hex 32)"
export REALTIME_INGESTION_AUTO_START=false
export PORT=18080 BIND_ADDRESS=127.0.0.1 ALLOWED_HOSTS=localhost,127.0.0.1
project="geneticgrid-smoke-${RANDOM}-$$"
compose=(docker compose -p "$project" -f compose.production.yml)
cleanup() {
  status=$?
  if [ "$status" -ne 0 ]; then "${compose[@]}" logs --no-color; fi
  "${compose[@]}" down -v
}
trap cleanup EXIT
"${compose[@]}" up -d --wait --wait-timeout 180
"${compose[@]}" exec -T backend python -m pytest tests/test_public_access.py tests/test_production_settings.py -q
"${compose[@]}" exec -T backend python - <<'PY'
import re
from urllib.request import urlopen
base = 'http://localhost:8000'
with urlopen(base + '/') as response:
    page = response.read().decode()
assets = re.findall(r'(?:src|href)="(/static/dist/[^\"]+\.(?:js|css))"', page)
assert assets, 'Built Vue assets were not referenced by the index'
assert 'name="tide-public-read-only" content="true"' in page
for asset in assets:
    with urlopen(base + asset) as response:
        assert response.status == 200, asset
with urlopen(base + '/api/sources/') as response:
    assert response.status == 200
print('Index, built assets, API and container health checks passed')
PY
