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
    'install_requires': ['SOAPpy-py3', 'tqdm'],
    'python_requires': '>=3.8',
    'extras_require': ['gdal', 'nose'],
    'packages': ['searchlaads'],
    'scripts': ['scripts/mod35_l2_example.py'],
    'name': 'searchLAADS'
}

setup(**config)

