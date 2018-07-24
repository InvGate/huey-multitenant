
class TaskRegistry(object):

    def __init__(self):
        self._registry = []

    def register(self, task, minute='*', hour='*', day_of_week='*', day='*', month='*'):
        self._registry.append({
            'task': task,
            'minute': minute,
            'hour': hour,
            'day_of_week': day_of_week,
            'day': day,
            'month': month,
        })

    def task_cron(self, task):
        return '{} {} {} {} {} {}\n'.format(task['minute'], task['hour'], task['day_of_week'], task['day'], task['month'], task['task'],)

    def get_periodic_tasks(self):
        return self._registry

registry = TaskRegistry()