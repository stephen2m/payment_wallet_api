import os
from datetime import timedelta
from os.path import join
from distutils.util import strtobool
import dj_database_url
import structlog
from celery.schedules import crontab
from configurations import Configuration

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Common(Configuration):
    INSTALLED_APPS = (
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',

        # Third party apps
        'rest_framework',
        'djmoney',
        'encrypted_fields',
        'corsheaders',

        # Our apps
        'api.apps.users',
        'api.apps.payments'
    )

    # https://docs.djangoproject.com/en/2.0/topics/http/middleware/
    MIDDLEWARE = (
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'corsheaders.middleware.CorsMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    )

    ALLOWED_HOSTS = ["*"]
    ROOT_URLCONF = 'api.urls'
    SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
    WSGI_APPLICATION = 'api.wsgi.application'

    # Email
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

    ADMINS = (
        ('Author', 'stephenmue@gmail.com'),
    )

    # Postgres
    DATABASES = {
        'default': dj_database_url.config(
            default='postgres://postgres:@postgres:5432/postgres',
            conn_max_age=int(os.getenv('POSTGRES_CONN_MAX_AGE', 600)),
        )
    }

    # General
    # Set DEBUG to False as a default for safety
    # https://docs.djangoproject.com/en/dev/ref/settings/#debug
    DEBUG = strtobool(os.getenv('DJANGO_DEBUG', 'False'))
    APPEND_SLASH = False
    TIME_ZONE = 'UTC'
    LANGUAGE_CODE = 'en-us'
    # If you set this to False, Django will make some optimizations so as not
    # to load the internationalization machinery.
    USE_I18N = False
    USE_L10N = True
    USE_TZ = True
    LOGIN_REDIRECT_URL = '/'

    # Static files (CSS, JavaScript, Images)
    # https://docs.djangoproject.com/en/2.0/howto/static-files/
    STATIC_ROOT = os.path.normpath(join(os.path.dirname(BASE_DIR), 'static'))
    STATICFILES_DIRS = []
    STATIC_URL = '/static/'
    STATICFILES_FINDERS = (
        'django.contrib.staticfiles.finders.FileSystemFinder',
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    )

    # Media files
    MEDIA_ROOT = join(os.path.dirname(BASE_DIR), 'media')
    MEDIA_URL = '/media/'

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': STATICFILES_DIRS,
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        },
    ]

    # Password Validation
    # https://docs.djangoproject.com/en/2.0/topics/auth/passwords/#module-django.contrib.auth.password_validation
    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
    ]

    DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt='iso'),
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(encoding='utf-8', errors='backslashreplace'),
            structlog.processors.ExceptionPrettyPrinter(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=structlog.threadlocal.wrap_dict(dict),
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    pre_chain = [
        # Add the log level and a timestamp to the event_dict if the log entry
        # is not from structlog.
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt='iso'),
    ]

    # Logging
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                '()': structlog.stdlib.ProcessorFormatter,
                'processor': structlog.processors.JSONRenderer(sort_keys=True),
                'foreign_pre_chain': pre_chain,
            },
        },
        'filters': {
            'require_debug_true': {
                '()': 'django.utils.log.RequireDebugTrue',
            },
        },
        'handlers': {
            'default': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'level': 'INFO'
            },
            'logtail': {
                'class': 'logtail.LogtailHandler',
                'formatter': 'default',
                'source_token': os.getenv('LOGTAIL_TOKEN')
            },
        },
        'loggers': {
            'api_requests': {
                'handlers': ['default', 'logtail'],
                'level': 'INFO',
                'propagate': False
            },
        }
    }

    # Custom user app
    AUTH_USER_MODEL = 'users.User'

    # Django Rest Framework
    # https://api.postman.com/collections/21819683-c38a83fd-d526-4ef6-a07e-1e82f038fe33?access_key=PMAT-01GMJ9R3PTZ40K77XP0Y4MXVWZ
    REST_FRAMEWORK = {
        'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
        'PAGE_SIZE': int(os.getenv('DJANGO_PAGINATION_LIMIT', 25)),
        'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S%z',
        'DEFAULT_RENDERER_CLASSES': [
            'rest_framework.renderers.JSONRenderer'
        ],
        'DEFAULT_PERMISSION_CLASSES': [
            'rest_framework.permissions.IsAuthenticated',
        ],
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework.authentication.SessionAuthentication',
            'rest_framework_simplejwt.authentication.JWTAuthentication',
        ),
        'DEFAULT_THROTTLE_CLASSES': [
            'rest_framework.throttling.AnonRateThrottle',
        ],
        'TEST_REQUEST_DEFAULT_FORMAT': 'json',
        'EXCEPTION_HANDLER': 'api.utils.exceptions.drf.core_exception_handler',
        'NON_FIELD_ERRORS_KEY': 'error',
    }

    # Simple JWT
    SIMPLE_JWT = {
        'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
        'REFRESH_TOKEN_LIFETIME': timedelta(seconds=31557600),
    }

    # Redis Settings
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': os.environ['REDIS_URL'],
        }
    }

    # Django Searchable Encrypted Fields
    # https://pypi.org/project/django-searchable-encrypted-fields/
    FIELD_ENCRYPTION_KEYS = [
        os.environ['FIELD_ENCRYPTION_KEY']
    ]

    # Celery config
    CELERY_BROKER_URL = os.environ['REDIS_URL']
    CELERY_RESULT_BACKEND = os.environ['REDIS_URL']
    CELERY_IMPORTS = ('api.apps.payments.tasks',)

    # Sentry Config
    SENTRY_DSN = os.getenv('SENTRY_DSN', None)
    if SENTRY_DSN:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.celery import CeleryIntegration

        sentry_sdk.init(SENTRY_DSN, integrations=[DjangoIntegration(), CeleryIntegration()])

    # Stitch Config
    LINKPAY_REDIRECT_URI = os.environ['LINKPAY_REDIRECT_URI']
    LINKPAY_USER_INTERACTION_URI = os.environ['LINKPAY_USER_INTERACTION_URI']
    STITCH_CLIENT_ID = os.environ['STITCH_CLIENT_ID']
    STITCH_CLIENT_SECRET = os.environ['STITCH_CLIENT_SECRET']
    STITCH_BENEFICIARY_ACCOUNT = {
        'bankId': os.environ['STITCH_BENEFICIARY_BANK_ID'],
        'name': os.environ['STITCH_BENEFICIARY_ACCOUNT_NAME'],
        'accountNumber': os.environ['STITCH_BENEFICIARY_ACCOUNT_NUMBER'],
        'accountType': os.environ['STITCH_BENEFICIARY_ACCOUNT_TYPE'],
        'beneficiaryType': os.environ['STITCH_BENEFICIARY_TYPE'],
    }

    # Webhook Config
    LINKPAY_WEBHOOK_SECRET_KEY = os.getenv('LINKPAY_WEBHOOK_SECRET_KEY')
    REFUND_WEBHOOK_SECRET_KEY = os.getenv('REFUND_WEBHOOK_SECRET_KEY')
