import py2app
from setuptools import setup


APP = ['main.py']
DATA_FILES = [
    'icons',
    'menubar.py',
    'slack_api.py'
]
OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'LSUIElement': True,
    },
    'packages': [
        'rumps',
        'slack',
        'aiohttp',
        'multidict'
    ],
    'iconfile': 'icons/slack1.png',
}

setup(
    app=APP,
    name='Slack Status Icon',
    version='0.1.0',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
