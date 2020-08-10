import os
import sys
import logging

INSTALLED_APPS = [
    'huey.contrib.djhuey',
    'huey_multitenant.contrib.djhuey_multitenant',
    'django_1.test_app',
]

HUEY = {
    'name': 'django-1',
    'consumer': {
        'loglevel': logging.DEBUG,
        'workers': 2,
        'scheduler_interval': 5,
    },
    'connection': {
        'port': 16379,
    },
}

HUEY_CHECK_MAINTENANCE = "django_1.test_app.maintenance.is_in_maintenance"

REDIS_PROTOCOL = 'redis'
REDIS_HOST = 'localhost'
REDIS_PORT = 16379
REDIS_DB = 0
REDIS_URL = u"{protocol}://{host}:{port}/{db}".format(protocol=REDIS_PROTOCOL,
                                                      host=REDIS_HOST,
                                                      port=REDIS_PORT,
                                                      db=REDIS_DB)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'KEY_PREFIX': 'django_1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient'
        }
    },
}

SECRET_KEY = 'foo'


PROJECT_ROOT = os.path.dirname(__file__)
ROOT = os.path.dirname(PROJECT_ROOT)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(ROOT, 'debug.log'),
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'huey': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
