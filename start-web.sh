#!/bin/bash

echo "Starting vtorprice"

set -euo pipefail

python manage.py collectstatic --no-input
python manage.py migrate

if [[ "$DJANGO_ENV" = "Production" ]]; then
  gunicorn -b 0.0.0.0:8000 \
    --log-level ${DJANGO_LOG_LEVEL,,} \
    --access-logfile - config.wsgi:application
else
  python manage.py runserver 0.0.0.0:8000
fi