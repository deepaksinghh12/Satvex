#!/bin/sh
set -e

# Run migrations and collectstatic then exec passed command
python manage.py makemigrations --noinput || true
python manage.py migrate --noinput
python manage.py collectstatic --noinput || true

exec "$@"
