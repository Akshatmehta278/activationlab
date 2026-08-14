#!/usr/bin/env sh
set -eu
python manage.py migrate --noinput
python manage.py collectstatic --noinput >/dev/null
if [ "${SEED_DEMO:-1}" = "1" ]; then
  python manage.py seed_demo --sessions 120 || true
fi
exec gunicorn activationlab.wsgi:application --bind 0.0.0.0:8000 --workers 2 --threads 4 --timeout 120
