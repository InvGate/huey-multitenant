import inspect
from huey.contrib.djhuey import periodic_task
from huey.api import crontab
from huey_multitenant.registry import registry

class PeriodicTask(object):

    def __init__(self, minute='*', hour='*', day_of_week='*', day='*', month='*'):
        self.minute = minute
        self.hour = hour
        self.day_of_week = day_of_week
        self.day = day
        self.month = month

    def __call__(self, f):
        registry.register(
            task='{}.{}'.format(inspect.getmodule(f).__name__, f.__name__),
            minute = self.minute,
            hour = self.hour,
            day_of_week = self.day_of_week,
            day = self.day,
            month = self.month
        )
        def wrapped_f(*args):
            f(*args)

        return periodic_task(crontab(
            month=self.month,
            day=self.day,
            day_of_week=self.day_of_week,
            hour=self.hour,
            minute=self.minute
        ))(wrapped_f)


