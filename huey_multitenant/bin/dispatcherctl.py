#!/usr/bin/env python

import click
import os

from huey_multitenant.core import Dispatcher


@click.command()
@click.option('--consumers', default=1, help='How many consumers are available.')
@click.option('--periodic', is_flag=True, help='Do you want to run periodic tasks ?')
@click.option('--verbose', is_flag=True, help='Verbose logging (includes DEBUG statements)')
@click.option('--logfile', default="", help='Redirect logs to file')
def dispatcher_main(consumers, periodic, verbose, logfile):

    conf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conf')
    Dispatcher(conf_path, consumers, periodic, verbose, logfile)


if __name__ == '__main__':
    dispatcher_main()
