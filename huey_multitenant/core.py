from concurrent.futures.thread import ThreadPoolExecutor
from configparser import ConfigParser
import logging
import os
import pickle
import sys
import time
from logging.handlers import RotatingFileHandler

from huey.consumer import ProcessEnvironment

from huey_multitenant.application import HueyApplication, HueyConsumer
from huey_multitenant.scheduler import Scheduler


class Dispatcher(object):
    """
    Main Dispatcher
    """
    def __init__(self, conf_path, max_consumers, periodic, verbose, logfile=None):
        self._total_consumers = max_consumers
        self.is_verbose = verbose
        self.tasks = []
        self.instances = []
        self.consumers = []

        self.setup_logger(logfile)

        self._logger.info('Init Dispatcher')
        self._logger.info('- Consumers = %d', max_consumers)
        self._logger.info('- Periodic  = %s', 'enabled' if periodic else 'disabled')
        self._logger.info('- Verbose   = %s', 'enabled' if verbose else 'disabled')

        self.setup_sentry(conf_path)
        self.load_config(conf_path)

        # Create the scheduler process (but don't start it yet).
        if periodic:
            scheduler = self._create_scheduler()
            self.scheduler = self._create_process(scheduler, 'Scheduler')
            self.scheduler.start()

        self.start()

    def _create_scheduler(self):
        return Scheduler(
            instances=self.instances,
            interval=60,
            utc=True)

    def _create_process(self, process, name):
        """
        Repeatedly call the `loop()` method of the given process. Unhandled
        exceptions in the `loop()` method will cause the process to terminate.
        """
        def _run():
            try:
                while True:
                    process.loop()
            except KeyboardInterrupt:
                pass
            except:
                self._logger.exception('Process %s died!', name)
        return ProcessEnvironment().create_process(_run, name)

    @property
    def loglevel(self):
        if self.is_verbose is False:
            return logging.INFO
        return logging.DEBUG

    def setup_logger(self, logfile):
        logformat = ('[%(asctime)s] %(levelname)s: %(message)s')
        loglevel = self.loglevel
        logging.basicConfig(level=loglevel, format=logformat)
        self._logger = logging.getLogger()

        if logfile:
            handler = RotatingFileHandler(logfile, maxBytes=1024 * 1024 * 100, backupCount=10)
            handler.setFormatter(logging.Formatter(logformat))
            self._logger.addHandler(handler)

    def setup_sentry(self, conf_path):
        key_path = os.path.join(conf_path, 'sentry.key')
        if os.path.isfile(key_path):
            with open(key_path, 'r') as f:
                sentry_key = f.read()

            self._logger.info('- Sentry initialized (%s)', sentry_key)
            import sentry_sdk
            sentry_sdk.init(sentry_key)
        else:
            self._logger.info('- Sentry not initialized')

    def load_config(self, conf_path):
        if not os.path.isdir(conf_path):
            self._logger.error('Applications not configured in %s', conf_path)
            conf_path = os.path.join('/etc', 'huey.multitenant.conf')

        if not os.path.isdir(conf_path):
            self._logger.error('Applications not configured in %s', conf_path)
            sys.exit(1)

        all_conf = (conf for conf in os.listdir(conf_path) if conf.endswith('.conf'))

        pool = ThreadPoolExecutor(16)
        instances = pool.map(lambda conf: self._load_instances_from_conf(conf, conf_path), all_conf)
        self.instances = [instance for instance in instances if instance is not None]
        pool.shutdown()
        if len(self.instances) == 0:
            self._logger.error('Check that you have almost one application configured in %s', conf_path)
            sys.exit(1)

    def _load_instances_from_conf(self, conf, conf_path):
        self._logger.info(conf)
        try:
            parser = ConfigParser()
            parser["DEFAULT"] = {
                'workers': '1',
                'worker-type': 'thread',
                'redis_host': 'localhost',
                'redis_port': '6379',
                'use_python3': 'false'
            }
            parser.read(os.path.join(conf_path, conf))
            for section in parser.sections():
                instance = HueyApplication(
                    name=parser.get(section, 'redis_prefix'),
                    python_path=parser.get(section, 'python'),
                    script_path=parser.get(section, 'script'),
                    workers=parser.get(section, 'workers'),
                    worker_type=parser.get(section, 'worker-type'),
                    settings=parser.get(section, 'settings'),
                    redis_host=parser.get(section, 'redis_host'),
                    redis_port=parser.get(section, 'redis_port'),
                    redis_prefix=parser.get(section, 'redis_prefix') or section,
                    use_python3=parser.getboolean(section, 'use_python3', fallback=False)
                )
        except Exception as e:
            self._logger.exception('Error reading config %s', conf)
            instance = None
        return instance

    def get_task_data(self, task):
        """Convert a message from the queue into a task"""
        raw = pickle.loads(task)
        if len(raw) == 7:
            task_id, klass_str, _, _, _, _, _ = raw
        elif len(raw) == 6:
            task_id, klass_str, _, _, _, _ = raw
        return task_id, klass_str

    def task_exists(self, task_id):
        for consumer in self.consumers:
            if consumer.task_id == task_id:
                return True
        return False

    def instance_is_active(self, instance):
        for consumer in self.consumers:
            if consumer.app == instance:
                return True
        return False

    def consume_task(self):
        for idx, _instance in enumerate(self.instances):
            tasks = _instance.get_pending_tasks()
            for _task in tasks:
                task_id, task_klass = self.get_task_data(_task)

                if not self.task_exists(task_id):
                    self._logger.info('Consume task: %s %s', task_klass, task_id)
                    self.consumers.append(HueyConsumer(_instance, task_id))
                    if len(self.instances) > 1:
                        self.instances.append(self.instances.pop(idx))
                    return True
        return False

    def start(self):
        self._logger.info('Start Dispatcher')
        timeout = 0.5
        while True:
            try:
                time.sleep(timeout)
                consumed = True
                while (len(self.consumers) < self._total_consumers) and consumed:
                    consumed = self.consume_task()

                self.consumers = [c for c in self.consumers if c.is_running()]

            except KeyboardInterrupt:
                self._logger.info('Received SIGINT')
                self.stop()
                break
            except:
                self._logger.exception('Error in consumer.')
                self.stop()
                break

    def stop(self):
        self._logger.info('Shutting down')
