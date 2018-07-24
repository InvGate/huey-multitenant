import os
from setuptools import setup, find_packages


with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as fh:
    readme = fh.read()

extras_require = {
    'backends': ("click", "huey", "redis"),
}

setup(
    name='huey multitenant',
    version=__import__('huey_multitenant').__version__,
    description='A dispatcher that allows using huey with multiple django applications',
    long_description=readme,
    author='InvGate Discover Team',
    author_email='neoassets@invgate.com',
    url='https://github.com/InvGate/huey-multitenant',
    packages=find_packages(),
    extras_require=extras_require,
    package_data={
        'huey_multitenant': [
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers :: DevOps',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    entry_points={
        'console_scripts': [
            'huey_multitenant_consumer = huey_multitenant.bin.dispatcherctl'
        ]
    },
    scripts=['huey_multitenant/bin/dispatcherctl.py'],
)
