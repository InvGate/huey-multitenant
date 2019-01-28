from __future__ import unicode_literals, absolute_import

from huey.consumer import Consumer
from huey.exceptions import ConfigurationError
import time
import threading
import os
import signal


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

        self._set_signal_handlers()

        original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
        if hasattr(signal, 'SIGHUP'):
            original_sighup_handler = signal.signal(signal.SIGHUP, signal.SIG_IGN)

        for _, worker_process in self.worker_threads:
            worker_process.start()

        signal.signal(signal.SIGINT, original_sigint_handler)
        if hasattr(signal, 'SIGHUP'):
            signal.signal(signal.SIGHUP, original_sighup_handler)

    def run(self):
        """
        Run the consumer.
        """
        start_time = time.time()
        self.start()
        time.sleep(1.0)
        for _, worker_process in self.worker_threads:
            worker_process.join()
        self._logger.info('Stop consumer. %s seconds' % (time.time() - start_time))
