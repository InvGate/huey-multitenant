"""
Create a logging filter for django handler, you can use it following:

from djhuey_multitenant.filters import skip_keyboard_interrupt
...
'filters': {
    'skip_keyboard_interrupt': {
        '()': 'django.utils.log.CallbackFilter',
        'callback': skip_keyboard_interrupt,
    }
},
'handlers': {
    'django': {
        'level': 'ERROR',
        'filters': ['skip_keyboard_interrupt'],
        'class': 'django.utils.log.AdminEmailHandler'
    }
},

"""
def skip_keyboard_interrupt(record):
    if record.exc_info:
        exc_type, exc_value = record.exc_info[:2]
        if isinstance(exc_value, KeyboardInterrupt):
            return False
    return True
