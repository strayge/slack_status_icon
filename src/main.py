import json
import os
from pathlib import Path

import rumps

from menu import Menu

app_name = 'slack_status_icon'
home = str(Path.home())
settings_filename = os.path.join(home, '.config', app_name, 'settings.json')

default_settings = '''
{
  "slack_token": "xoxs-******************"
}
'''


def read_settings():
    if not os.path.exists(settings_filename):
        os.makedirs(os.path.dirname(settings_filename), exist_ok=True)
        with open(settings_filename, 'wt') as f:
            f.write(default_settings)
    with open(settings_filename, 'rt') as f:
        settings = json.load(f)
    if '*' in settings.get('slack_token'):
        return
    return settings


if __name__ == '__main__':
    settings = {}
    try:
        settings = read_settings()
        if not settings:
            rumps.alert(f"SlackIcon: need valid token in:\n{settings_filename}")
            exit(1)
    except Exception as e:
        rumps.alert(f"SlackIcon: can't read settings:\n{e}")
        exit(1)

    slack_token = settings.get('slack_token')
    menu = Menu(slack_token=slack_token)
    menu.run()
