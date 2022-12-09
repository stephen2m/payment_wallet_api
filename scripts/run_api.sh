#!/bin/bash

export APP_MODULE=${APP_MODULE-api.wsgi:application}
export APP_HOST=${APP_HOST:-0.0.0.0}
export APP_PORT=${APP_PORT:-8000}

python scripts/wait_for_postgres.py
python manage.py migrate --noinput
python manage.py runserver "$APP_HOST":"$APP_PORT" --nostatic
