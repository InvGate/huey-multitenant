#!/usr/bin/env python

import click
import os

from huey_multitenant.core import Dispatcher

@click.command()
@click.option('--consumers', default=1, help='How many consumers are available.')
@click.option('--periodic', default=True, help='Do you want to run periodic tasks ?')
@click.option('--verbose', default=False, help='Verbose logging (includes DEBUG statements)')
def dispatcher_main(consumers, periodic, verbose):

    conf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conf')
    Dispatcher(conf_path, consumers, periodic, verbose)

if __name__ == '__main__':
    dispatcher_main()

