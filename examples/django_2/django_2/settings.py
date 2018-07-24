import logging
import os
import sys


INSTALLED_APPS = [
    'huey.contrib.djhuey',
    'huey_multitenant.contrib.djhuey_multitenant',
    'django_2.test_app',
]

HUEY = {
    'name': 'django_2',
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
            'propagate': True,
        },
        'django': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}