import json
import os
from pathlib import Path

import rumps


APP_ICON = os.path.join('icons', 'app.icns')
EMPTY_ICON = os.path.join('icons', 'slack.png')

APP_NAME = 'Slack Status Icon'
APP_NAME_LOWER = 'slack_status_icon'


class Settings:
    def __init__(self):
        home = str(Path.home())
        self._filename = os.path.join(home, '.config', APP_NAME_LOWER, 'settings.json')
        # default values
        self._storage = {
            'slack_token': "xoxs-******************",
            'update_interval': 10,
            'channels_update_interval': 20 * 60,
        }
        self.load()

    @staticmethod
    def notify(text):
        rumps.notification(APP_NAME, '', text, icon=APP_ICON, sound=False)

    def load(self):
        if not os.path.exists(self._filename):
            return
        with open(self._filename, 'rt') as f:
            try:
                self._storage = json.load(f)
            except Exception:
                self.notify('Invalid config')

    def save(self):
        self._create_path()
        with open(self._filename, 'wt') as f:
            json.dump(self._storage, f)

    def _create_path(self):
        if not os.path.exists(self._filename):
            os.makedirs(os.path.dirname(self._filename), exist_ok=True)

    @property
    def is_valid(self):
        return '*' in self._storage.get('slack_token', '*')

    @property
    def token(self):
        return self._storage.get('slack_token')

    @property
    def update_interval(self):
        return self._storage.get('update_interval')

    @property
    def channels_update_interval(self):
        return self._storage.get('channels_update_interval')

    def set_token(self, token):
        self._storage['slack_token'] = token
        self.save()
