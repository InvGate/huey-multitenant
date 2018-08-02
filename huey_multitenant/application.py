import subprocess
import logging
import os
import signal
import threading
import time

from huey.storage import RedisStorage
from huey import crontab


class HueyApplication(object):
    """
    Huey App Instance
    """

    def __init__(self, name, python_path, script_path, workers):
        self._logger = logging.getLogger()
        self._logger.info('Register App: %s', name)

        self.storage = RedisStorage(name)
        self.name = name
        self.workers = workers
        self.python_path = python_path
        self.script_path = script_path

        self.periodic_tasks = []
        self.load_periodic_tasks()

    def load_periodic_tasks(self):
        """
        This method read schedule.info file from the instance. At the same folder level that manage.py file.

        :return:
        """
        schedule_process = self.execute_command('makeschedule')
        while self.is_running(schedule_process):
            time.sleep(0.5)

        if os.path.isfile(os.path.join(os.path.dirname(self.script_path), 'schedule.info')):
            self._logger.debug('Schedule info created')
        else:
            self._logger.debug('Schedule info not found')
            return

        info_file = os.path.join(os.path.dirname(self.script_path), 'schedule.info')
        with open(info_file, 'r') as f:
            lines = f.readlines()

        for ln in lines:
            ln = ln.rstrip().strip().rstrip()
            if ln.startswith(';') or ln.startswith('#'):
                continue

            info = ln.split()
            if len(info) == 6:
                self._logger.debug('Added periodic method: %s', ln)
                self.periodic_tasks.append({
                    'method': info[5],
                    'validate_datetime': crontab(
                        minute=info[0],
                        hour=info[1],
                        day_of_week=info[2],
                        day=info[3],
                        month=info[4])
                })
            elif len(info) > 1:
                self._logger.info('Invalid cron line.')

        if len(self.periodic_tasks) == 0:
            self._logger.info('No periodic task found')

    def get_pending_tasks(self):
        """
        Returns list of pending tasks.
        """
        return self.storage.enqueued_items()

    def get_periodic_tasks(self, now):
        """
        Returns list of periodic tasks.
        """
        return [task for task in self.periodic_tasks if task['validate_datetime'](now)]

    def is_running(self, process):
        try:
            if process.poll() is None:
                return True
            else:
                process.communicate()
            # os.kill(process.pid, 0)
        except OSError:
            return False
        return False

    def execute_command(self, command):
        """
        Execute manage.py command.

        :param command: (str) command to be executed
        :return: process id
        """
        cmd = [self.python_path, self.script_path]
        if command:
            cmd.extend(command.split())

        self._logger.debug('Execute: {}'.format(cmd))

        process = subprocess.Popen(
            cmd,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

        self._logger.debug('PID: {}'.format(process.pid))
        return process


class HueyConsumer():
    def __init__(self, instance, task_id):
        self.app = instance
        self.task_id = task_id
        self.process = None
        self.consume()

    def is_running(self):
        return self.app.is_running(self.process)

    def kill_consumer(self):
        os.kill(self.process.pid, signal.SIGINT)

    def consume(self):
        self.process = self.app.execute_command('run_huey --no-periodic -w %d' % self.app.workers)
        threading.Timer(1, self.kill_consumer).start()