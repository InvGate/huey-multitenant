import logging
import datetime
import time

from huey.consumer import BaseProcess

class Scheduler(BaseProcess):
    """
    Scheduler handles enqueueing tasks when they are scheduled to execute. Note
    that the scheduler does not actually execute any tasks, but simply enqueues
    them so that they can be picked up by the worker processes.

    If periodic tasks are enabled, the scheduler will wake up every 60 seconds
    to enqueue any periodic tasks that should be run.
    """
    def __init__(self, instances, interval, utc):
        self._logger = logging.getLogger()
        self._logger.info('Init Scheduler')

        self.instances = instances
        self.interval = min(interval, 60)
        self.utc = utc
        self._counter = 0
        self._q, self._r = divmod(60, self.interval)
        self._cr = self._r
        self._next_loop = time.time()

    def get_now(self):
        if self.utc:
            return datetime.datetime.utcnow()
        return datetime.datetime.now()

    def sleep_for_interval(self, start_ts, nseconds):
        """
        Sleep for a given interval with respect to the start timestamp.

        So, if the start timestamp is 1337 and nseconds is 10, the method will
        actually sleep for nseconds - (current_timestamp - start_timestamp). So
        if the current timestamp is 1340, we'll only sleep for 7 seconds (the
        goal being to sleep until 1347, or 1337 + 10).
        """
        sleep_time = nseconds - (time.time() - start_ts)
        if sleep_time <= 0:
            return
        self._logger.debug('Sleeping for %s', sleep_time)
        # Recompute time to sleep to improve accuracy in case the process was
        # pre-empted by the kernel while logging.
        sleep_time = nseconds - (time.time() - start_ts)
        if sleep_time > 0:
            time.sleep(sleep_time)

    def loop(self, now=None):
        current = self._next_loop
        self._next_loop += self.interval
        if self._next_loop < time.time():
            self._logger.info('scheduler skipping iteration to avoid race.')
            return

        # The scheduler has an interesting property of being able to run at
        # intervals that are not factors of 60. Suppose we ask our
        # scheduler to run every 45 seconds. We still want to schedule
        # periodic tasks once per minute, however. So we use a running
        # remainder to ensure that no matter what interval the scheduler is
        # running at, we still are enqueueing tasks once per minute at the
        # same time.
        if self._counter >= self._q:
            self._counter = 0
            if self._cr:
                self.sleep_for_interval(current, self._cr)
            if self._r:
                self._cr += self._r
                if self._cr >= self.interval:
                    self._cr -= self.interval
                    self._counter -= 1

            self.enqueue_periodic_tasks(now or self.get_now(), current)
        self._counter += 1

        self.sleep_for_interval(current, self.interval)

    def enqueue_periodic_tasks(self, now, start):
        for app in self.instances:
            for task in app.get_periodic_tasks(now):
                self._logger.info('Scheduling periodic task %s.', task)
                app.execute_command(task['method'])

        return True