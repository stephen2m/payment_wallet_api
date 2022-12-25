#!/bin/bash

until cd /code/api
do
    echo 'Waiting for server volume...'
done

celery -A celery_app worker --loglevel=info --concurrency 1 -E
