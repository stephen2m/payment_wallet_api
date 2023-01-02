import os
from .common import Common


class Production(Common):
    # Set DEBUG to False as a default for safety
    # https://docs.djangoproject.com/en/dev/ref/settings/#debug
    DEBUG = False

    INSTALLED_APPS = Common.INSTALLED_APPS
    SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

    # Site
    # https://docs.djangoproject.com/en/2.0/ref/settings/#allowed-hosts
    ALLOWED_HOSTS = [".cloud.okteto.net"]
    INSTALLED_APPS += ("gunicorn",)

    CORS_ALLOWED_ORIGINS = [
        'https://paiment-stephen2m.cloud.okteto.net'
    ]
