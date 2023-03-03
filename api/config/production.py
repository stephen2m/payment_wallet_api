import os
from .common import Common


class Production(Common):
    INSTALLED_APPS = Common.INSTALLED_APPS
    SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

    # Site
    # https://docs.djangoproject.com/en/2.0/ref/settings/#allowed-hosts
    # ALLOWED_HOSTS will be a space-separated string, so convert it to a list
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS').split(' ')
    INSTALLED_APPS += ("gunicorn",)

    # CORS_ALLOWED_ORIGINS will be a space-separated string, so convert it to a list
    CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS').split(' ')
