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
    'version': '0.3',
    'install_requires': ['nose', 'SOAPpy', 'tqdm', "gdal"],
    'packages': ['searchlaads'],
    'scripts': ['scripts/mod35_l2_example.py'],
    'name': 'searchLAADS'
}

setup(**config)

