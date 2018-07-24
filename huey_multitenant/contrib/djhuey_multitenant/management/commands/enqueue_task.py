import importlib
import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Execute the task passed in params. Full path.'

    def add_arguments(self, parser):
        parser.add_argument('task', type=str)

    def handle(self, *args, **options):
        function_string = options['task']
        mod_name, func_name = function_string.rsplit('.', 1)
        mod = importlib.import_module(mod_name)
        func = getattr(mod, func_name)
        if callable(func):
            func()

