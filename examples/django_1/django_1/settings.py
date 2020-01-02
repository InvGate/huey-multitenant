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
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'DEBUG'
        },
    },
}