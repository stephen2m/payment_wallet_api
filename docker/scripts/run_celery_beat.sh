#!/bin/sh

until cd /code/api
do
    echo 'Waiting for server volume...'
done

celery -A celery_app beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
