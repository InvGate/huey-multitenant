#!/usr/bin/python
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser  # ver. < 3.0
import json
import os
import time
import subprocess
import argparse
import sentry_sdk

class HueyHealthException(Exception):
    def __init__(self, app_data):
        super(HueyHealthException, self).__init__()
        self.seconds = app_data['seconds']
        self.redis_prefix = app_data['redis_prefix']
        self.health = app_data['health']
        self.server_name = app_data['server_name']


class HueyApp:
    def __init__(self, settings, python, manage):
        self.settings = settings
        self.python = python
        self.manage = manage

    def execute_command(self, command):
        """
        Execute manage.py command.

        :param command: (str) command to be executed
        :return: process id
        """
        cmd = [self.python, self.manage]
        if command:
            cmd.extend(command.split())

        process = subprocess.Popen(
            cmd,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        out, err = process.communicate()
        return out

    def check_health(self):
        run_cmd = 'check_periodic_task_health'
        if self.settings is not None:
            run_cmd = run_cmd + ' --settings %s' % self.settings
        out = self.execute_command(run_cmd)
        data = json.loads(out.splitlines()[1])
        if data['health'] == 'DANGER':
            raise HueyHealthException(data)


def load_config(conf_path):
    apps = []
    for conf in os.listdir(conf_path):
        if conf.endswith('.conf'):
            parser = ConfigParser({
                'workers': '1',
                'worker-type': 'thread',
                'settings': None
            })
            parser.read(os.path.join(conf_path, conf))
            for section in parser.sections():
                apps.append(HueyApp(
                    settings=parser.get(section, 'settings'),
                    python=parser.get(section, 'python'),
                    manage=parser.get(section, 'script')
                ))
    return apps


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Health Checker.')
    parser.add_argument('--timeout', type=int, default=60, help='Timeout seconds for check. Default is 60 seconds.')
    args = parser.parse_args()

    sentry_sdk.init("https://2bbc232c49af4e0ba34f13d3eb0804dd@sentry.io/1303179")
    conf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conf')
    apps = load_config(conf_path)
    while True:
        try:
            time.sleep(args.timeout)
            for app in apps:
                app.check_health()
        except KeyboardInterrupt:
            print('bye')
            break
        except Exception as e:
            sentry_sdk.capture_exception(e)
            break
