import imp
import logging
import sys

from django.apps import apps as django_apps
from django.conf import settings
from django.core.management.base import BaseCommand

from huey.consumer_options import ConsumerConfig
from huey.consumer_options import OptionParserHandler

from huey_multitenant.consumer import ExecuteConsumer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Execute Task consumer. Example usage::

    To start the consumer (note you must export the settings module):

    django-admin.py execute_task
    """
    help = "Run the queue consumer, execute one task and die."
    _type_map = {'int': int, 'float': float}

    def add_arguments(self, parser):
        option_handler = OptionParserHandler()
        groups = (
            option_handler.get_logging_options(),
            option_handler.get_worker_options(),
            option_handler.get_scheduler_options(),
        )
        for option_list in groups:
            for short, full, kwargs in option_list:
                if short == '-v':
                    full = '--huey-verbose'
                    short = '-V'
                if 'type' in kwargs:
                    kwargs['type'] = self._type_map[kwargs['type']]
                kwargs.setdefault('default', None)
                parser.add_argument(full, short, **kwargs)

    def autodiscover(self):
        """Use Django app registry to pull out potential apps with tasks.py module."""
        module_name = 'tasks'
        for config in django_apps.get_app_configs():
            app_path = config.module.__path__
            try:
                fp, path, description = imp.find_module(module_name, app_path)
            except ImportError:
                continue
            else:
                import_path = '%s.%s' % (config.name, module_name)
                try:
                    imp.load_module(import_path, fp, path, description)
                except ImportError:
                    logger.exception('Found "%s" but error raised attempting '
                                     'to load module.', import_path)

    def handle(self, *args, **options):
        from huey.contrib.djhuey import HUEY

        consumer_options = {}
        try:
            if isinstance(settings.HUEY, dict):
                consumer_options.update(settings.HUEY.get('consumer', {}))
        except AttributeError:
            pass

        for key, value in options.items():
            if value is not None:
                consumer_options[key] = value

        consumer_options.setdefault('verbose',
                                    consumer_options.pop('huey_verbose', None))
        consumer_options['periodic'] = False
        self.autodiscover()

        config = ConsumerConfig(**consumer_options)
        config.validate()
        config.setup_logger()

        consumer = ExecuteConsumer(HUEY, **config.values)
        consumer.run()
