#!/bin/bash

export APP_MODULE=${APP_MODULE-api.wsgi:application}
export APP_HOST=${APP_HOST:-0.0.0.0}
export APP_PORT=${APP_PORT:-8000}

python docker/scripts/wait_for_postgres.py
python manage.py migrate --noinput

gunicorn api.wsgi --bind "$APP_HOST":"$APP_PORT"
#python manage.py runserver "$APP_HOST":"$APP_PORT" --nostatic
