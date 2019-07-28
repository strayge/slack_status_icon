from setuptools import setup


APP = ['src/main.py']
DATA_FILES = [
    'icons',
    'src',
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
        'multidict',
        'requests',
    ],
    'iconfile': 'icons/app.icns',
}

setup(
    app=APP,
    name='Slack Status Icon',
    version='0.3.0',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
