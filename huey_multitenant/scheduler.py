import logging
import pickle
import datetime
import uuid
import time

from huey.consumer import BaseProcess
from huey.exceptions import ScheduleReadException
from huey.exceptions import QueueWriteException


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

    def loop(self, now=None):
        current = self._next_loop
        self._next_loop += self.interval
        if self._next_loop < time.time():
            self._logger.info('scheduler skipping iteration to avoid race.')
            return

        try:
            for app in self.instances:
                task_list = app.get_schedule(now or self.get_now())
                for task in task_list:
                    self.enqueue_task(app, task)
        except ScheduleReadException:
            self._logger.exception('Error reading from task schedule.')

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
                # TODO: En lugar de llamar al comando enqueue_task se genera la entrada en Redis a mano.
                self._logger.info('Scheduling periodic task %s.', task)
                msg = pickle.dumps((
                    str(uuid.uuid4()),
                    'queue_task_{}'.format(task['method'].split('.')[-1]),
                    None,
                    0,
                    0,
                    ((), {}),
                    None), protocol=2)
                app.storage.enqueue(msg)

        return True

    def enqueue_task(self, app, task):
        """
        Convenience method for enqueueing a task.
        """
        try:
            self._logger.info('Enqueue %s for execution', task)
            app.storage.enqueue(task)
        except QueueWriteException:
            self._logger.exception('Error enqueueing task: %s', task)
        else:
            self._logger.debug('Enqueued task: %s', task)