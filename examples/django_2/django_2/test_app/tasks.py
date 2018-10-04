from huey.contrib.djhuey import task
from huey_multitenant.contrib.djhuey_multitenant import PeriodicTask

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@task()
def simple_task(number):
    logger.debug('[APP 2] simple_task with param (%d)' % number)
    return number

@PeriodicTask()
def every_minute_task():
    logger.debug('{}:{} [APP 2] Every minute'.format(datetime.now().hour, datetime.now().minute))

@PeriodicTask(minute='*/2')
def two_minute_task():
    logger.debug('{}:{} [APP 2] Every two minute'.format(datetime.now().hour, datetime.now().minute))

#
# @PeriodicTask(minute='21')
# def exact_task_one():
#     logger.debug('[TASK] Every N minutes')

# @PeriodicTask(minute='45')
# def exact_task_two():
#     logger.debug('[TASK] Every NN minutes')
