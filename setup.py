try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Search LAADS web for MODIS files.',
    'author': 'Benjamin Roesner',
    'url': 'https://github.com/BENR0/searchLAADs',
    'download_url': 'https://github.com/BENR0/searchLAADs',
    'author_email': '.',
    'version': '0.1',
    'install_requires': ['nose', 'SOAPpy', 'progressbar2'],
    'packages': ['searchlaads'],
    'scripts': ['scripts/mod35_l2.py'],
    'name': 'searchLAADS'
}

setup(**config)

