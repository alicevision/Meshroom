from setuptools import setup


setup(
    name='meshroom-headless',
    version='0.1.0',
    description='Meshroom headless',
    install_requires=['psutil', 'requests'],
    packages=['meshroom'],
    scripts=[
        'bin/meshroom_batch',
        'bin/meshroom_compute',
        'bin/meshroom_newNodeType',
        'bin/meshroom_statistics',
        'bin/meshroom_status',
        'bin/meshroom_submit'
    ]
)
