Huey Multitenant - A dispatcher that allows using huey with multiple django applications
========================================================================================

I used this project with:

- Python 2.7.10, Python 3.6.5
- Redis 3.2.9,
- Django 1.11.8 apps
- Huey 1.10.0

First, create a virtualenv and install the requirements.

.. code-block:: console

    $ pip install -r requirements.txt

Point to some Django instances in config folder, copy default config file and modify it:

.. code-block:: console

    $ cp conf/default conf/instance-name.conf

In the django instances you must add djhuey_multitenant app into INSTALLED_APPS.
Also replace the huey periodic decorator with the mutitenant decorator

Replace

.. code-block:: python

    from huey.contrib.djhuey import periodic_task

    @periodic_task(crontab(minute='0', hour='3'))
    def nightly_backup():
        sync_all_data()

With

.. code-block:: python

    from huey_multitenant.contrib.djhuey_multitenant import PeriodicTask

    @PeriodicTask(minute='0', hour='3')
    def nightly_backup():
        sync_all_data()


Activate virtualenv and launch the dispatcher:

.. code-block:: console

    $ python dispatcherctl.py --consumers 4 --periodic true --verbose true

This will create a schedule.info file inside each django instance with peridic tasks information and run the dispatcher.

Examples
========

To run the examples make sure that the redis server is up.

Install Django.

Create a symbolic link inside your virtualenv site-packages to the huey_multitenant folder.

Create django1.conf file inside bin/conf folder with this content (replace PATH):

.. code-block:: python

    [django1]
    python=PATH/.venv/bin/python
    script=PATH/examples/django_1/manage.py
    worker-type=thread
    workers=1


Create django2.conf file inside bin/conf folder with this content (replace PATH):

.. code-block:: python

    [django2]
    python=PATH/.venv/bin/python
    script=PATH/examples/django_2/manage.py
    worker-type=thread
    workers=1

Launch the dispatcher in a terminal

.. code-block:: console

    $ python dispatcherctl.py --consumers 4 --periodic true --verbose true

In other terminal go to the examples/django_N folder and run

.. code-block:: console

    $ python manage.py shell

Now put some tasks in queue

.. code-block:: python

    from django_N.test_app.tasks import long_task
    long_task()

