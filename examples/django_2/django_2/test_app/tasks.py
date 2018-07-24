from huey.contrib.djhuey import task, db_task
from huey_multitenant.contrib.djhuey_multitenant import PeriodicTask

import logging
import time

logger = logging.getLogger(__name__)

def no_task(number):
    logger.debug('[NO TASK](%d)' % number)
    return number

@task()
def simple_task(number):
    logger.debug('[TASK] simple_task with param (%d)' % number)
    return number

@db_task()
def long_task(number):
    logger.debug('[TASK] Long with param (%s)' % number)
    time.sleep(30) # Thirty seconds
    logger.debug('[TASK] finished')

@PeriodicTask(minute='*/2')
def two_minute_task():
    logger.debug('[TASK] Every Two minutes ')

@PeriodicTask(minute='*/3')
def three_minute_task():
    logger.debug('[TASK] Every Three minutes')

