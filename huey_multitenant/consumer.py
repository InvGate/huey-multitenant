from __future__ import unicode_literals, absolute_import

from django.conf import settings
from django.utils.module_loading import import_string
from huey.consumer import Consumer, EVENT_FINISHED, EVENT_STARTED
from huey.exceptions import ConfigurationError
from time import sleep
from datetime import timedelta, datetime
import os
from json import loads


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

    def _stop_when_idle(self, start_time, timeout=20.0):
        """
        Stops the workers as soon as they are idle.
        With a maximum of timeout seconds
        """

        last_finished = datetime.utcnow()
        working = False

        def has_timed_out():
            self._logger.debug("Checking total time")
            return datetime.utcnow() > (start_time + timedelta(seconds=timeout))
        
        def is_idle_since(idle_timeout=1.):
            self._logger.debug("Checking idle time")
            return (datetime.utcnow() > (last_finished + timedelta(seconds=idle_timeout))) and not working

        listener = self.huey.storage.listener()

        while True:
            message = listener.get_message(ignore_subscribe_messages=True, timeout=0.5)
            if message:
                event = loads(message['data'].decode('utf-8'))
                self._logger.debug("Got event from worker: {}".format(event))
                if event and 'status' in event:
                    if event['status'] == EVENT_FINISHED:
                        last_finished = datetime.utcnow()
                        working = False
                    elif event['status'] == EVENT_STARTED:
                        working = True
                    else:
                        # We may need to handle extra messages differently
                        working = False

            if has_timed_out() or is_idle_since():
                self._stop_worker()
                return
            

    def _stop_worker(self):
        self._logger.debug('Sending stop signal to workers')
        self.stop_flag.set()
        for _, worker_process in self.worker_threads:
            worker_process.join()
        

    def run(self):
        """
        Run the consumer.
        """
        self._logger.info('Start consumer.')
        start_time = datetime.utcnow()

        self.check_maintenance_mode()
        self.start()

        self._stop_when_idle(start_time)

        total_seconds = (datetime.utcnow() - start_time).total_seconds()
        self._logger.info('Stop consumer. %s seconds' % total_seconds)
        exit(0)
