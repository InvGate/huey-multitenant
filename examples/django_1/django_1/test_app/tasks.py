from huey.contrib.djhuey import task
from huey_multitenant.contrib.djhuey_multitenant import PeriodicTask

from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)

@task()
def simple_task(number):
    logger.debug('[APP 1] simple_task with param (%d)' % number)
    return number

@task()
def simple_log():
    logger.debug('[APP 1] debug')
    logger.info('[APP 1] info')
    logger.error('[APP 1] error' )

@task()
def long_task(number):
    logger.debug('[APP 1] long_task with param (%d)' % number)
    time.sleep(number)
    logger.debug('-- DONE (%d)' % number)
    return number

# @PeriodicTask(minute='*/1')
# def one_minute_task():
#     logger.debug('[TASK] Every One minute ')

# @PeriodicTask(minute='19')
# def exact_task_one():
#     logger.debug('[TASK] Every N minutes')

# @PeriodicTask()
# def every_minute():
#     logger.debug('{}:{} [APP 1] Every minute'.format(datetime.now().hour, datetime.now().minute))
