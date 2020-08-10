import datetime
import subprocess
import logging
import os
from pickle import loads, UnpicklingError
import signal
import threading
import time

from huey.storage import RedisStorage
from huey import crontab


MAX_SECONDS_RUNNING = 15 * 60   # 15 minutes


class HueyApplication(object):
    """
    Huey App Instance
    """

    def __init__(self,
                 name,
                 python_path,
                 script_path,
                 workers,
                 worker_type,
                 settings,
                 redis_host,
                 redis_port,
                 redis_prefix,
                 redis_maintenance_key,
                 use_python3=False):
        self._logger = logging.getLogger()
        self._logger.info('\nRegister App: %s\nWorker Type: %s\nWorkers: %s', name, worker_type, workers)

        self.storage = RedisStorage(
            name=redis_prefix,
            host=redis_host,
            port=redis_port)
        self.name = name
        self.redis_maintenance_key = redis_maintenance_key
        self.workers = workers
        if worker_type in ['process', 'greenlet']:
            self.worker_type = worker_type
        else:
            self.worker_type = 'thread'
        self.settings = settings
        self.python_path = python_path
        self.script_path = script_path

        self.periodic_tasks = []
        self.use_python3 = use_python3
        self.load_periodic_tasks()

    def is_in_maintenance_mode(self):
        # CAUTION: If you change the logic to decide if the system
        # is in maintenance mode or not, also change it in neo-assets
        encoded_data = self.storage.conn.get(self.redis_maintenance_key)
        if encoded_data is None:
            return False
        try:
            return loads(encoded_data)
        except UnpicklingError:
            self._logger.error('Error unpickling maintenance mode key {}, using maintenance mode off'.format(
                self.redis_maintenance_key))
            return False

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
                self._logger.info('Added periodic method: %s', ln)
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

    def get_schedule(self, ts):
        return self.storage.read_schedule(ts)

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

    def kill_process(self, process):
        self._logger.error('[{}] kill_huey PID: {}'.format(self.name, process.pid))
        os.kill(process.pid, signal.SIGKILL)

    def execute_command(self, command):
        """
        Execute manage.py command.

        :param command: (str) command to be executed
        :return: process id
        """
        cmd = [self.python_path, self.script_path]
        if command:
            cmd.extend(command.split())

        if self.settings is not None:
            cmd.extend(['--settings', self.settings])

        self._logger.debug('[{}] Execute: {}'.format(self.name, cmd))

        process = subprocess.Popen(
            cmd,
            shell=False)

        process_name = cmd[2]
        if process_name == 'enqueue_task':
            process_name = '{} {}'.format(process_name, cmd[3])

        self._logger.info('[{}] {} PID: {}'.format(self.name, process_name, process.pid))
        return process


class HueyConsumer:
    def __init__(self, instance, task_id):
        self.app = instance
        self.task_id = task_id
        self.process = None
        self.start_at = datetime.datetime.now()
        self.consume()

    def is_running(self):
        running = self.app.is_running(self.process)
        if running:
            if (datetime.datetime.now() - self.start_at).seconds > MAX_SECONDS_RUNNING:
                self.start_at = datetime.datetime.now()
                self.kill_consumer()

        return running

    def kill_consumer(self):
        self.app.kill_process(self.process)

    def consume(self):
        run_cmd = 'execute_task --no-periodic -k %s -w %s' % (self.app.worker_type, self.app.workers)

        self.process = self.app.execute_command(run_cmd)

        # Wait 10 seconds until send the sigint signal.
        # In that time the workers can handle more tasks
        # threading.Timer(10, self.kill_consumer).start()
