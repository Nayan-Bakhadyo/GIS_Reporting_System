from setuptools import setup

APP = ['gis_reporting_system.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['tkinter'],
    'includes': ['matplotlib', 'matplotlib.backends.backend_tkagg', 'numpy'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
