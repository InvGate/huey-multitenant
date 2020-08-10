from __future__ import unicode_literals, absolute_import

from django.conf import settings
from django.utils.module_loading import import_string
from huey.consumer import Consumer
from huey.exceptions import ConfigurationError
import time
import os


class ExecuteConsumer(Consumer):
    """
    This consumer execute one task and die. Doesn't loads any Scheduler.
    """

    def _create_process(self, process, name):
        if process is None:
            return None

        return super(ExecuteConsumer, self)._create_process(process, name)

    def _create_scheduler(self):
        return None

    def start(self):
        """
        Start all consumer processes and register signal handlers.
        Don't init scheduler.
        """
        if self.huey.always_eager:
            raise ConfigurationError(
                'Consumer cannot be run with Huey instances where always_eager'
                ' is enabled. Please check your configuration and ensure that'
                ' "huey.always_eager = False".')
        # Log startup message.
        self._logger.info('Huey consumer started with %s %s, PID %s',
                          self.workers, self.worker_type, os.getpid())
        self._logger.info('Scheduler disabled')
        self._logger.info('Health checker is %s',
                          'enabled' if self._health_check else 'disabled')
        self._logger.info('Periodic tasks are %s.',
                          'enabled' if self.periodic else 'disabled')
        self._logger.info('UTC is %s.', 'enabled' if self.utc else 'disabled')

        for _, worker_process in self.worker_threads:
            worker_process.start()

    def check_maintenance_mode(self):
        if hasattr(settings, 'HUEY_CHECK_MAINTENANCE'):
            maintenance_path = settings.HUEY_CHECK_MAINTENANCE
            is_maintenance_on = import_string(maintenance_path)
            if is_maintenance_on():
                self._logger.info('MaintenanceMode is on, stopping consumer')
                exit(0)

    def run(self):
        """
        Run the consumer.
        """
        self._logger.info('Start consumer.')
        start_time = time.time()

        self.check_maintenance_mode()
        self.start()
        time.sleep(1.0)
        self.stop_flag.set()
        for _, worker_process in self.worker_threads:
            worker_process.join()
        self._logger.info('Stop consumer. %s seconds' % (time.time() - start_time))
        exit(0)
