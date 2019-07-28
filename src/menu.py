import logging
import os
import time

import rumps

from settings import (
    APP_ICON,
    EMPTY_ICON,
    Settings,
)
from slack_api import Slack

logger = logging.getLogger(__name__)


def get_icon(count: int) -> str:
    if count <= 0:
        return EMPTY_ICON
    if count < 10:
        return os.path.join('icons', f'slack{count}.png')
    return os.path.join('icons', 'slack_more.png')


class MenuItem(rumps.MenuItem):
    def __init__(self, *args, channel_id: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel_id = channel_id


class Menu(rumps.App):
    def __init__(self):
        super().__init__('Slack', icon=EMPTY_ICON, quit_button=None)
        self.settings = Settings()
        self.slack = None
        self.init_slack()
        self.last_check = 0
        self.last_check_channels = 0

        menuitem_open = MenuItem('Open', channel_id='', callback=self.open_slack, key='o')
        menuitem_quit = MenuItem('Quit', callback=rumps.quit_application, key='q')
        menuitem_settings = MenuItem('Settings', callback=self.open_settings, key='s')
        self.menu_items_header = [menuitem_open]
        self.menu_items_footer = [menuitem_settings, menuitem_quit]

    def init_slack(self):
        token = None
        cookie = None
        if self.settings.token.startswith('xoxs'):
            token = self.settings.token
        elif 'd=' in self.settings.token:
            cookie = self.settings.token
        self.slack = Slack(token=token, cookie=cookie)
        if not self.slack.auth:
            token = self.settings.token[:4] + '...' + self.settings.token[-4:]
            self.settings.notify(f'Invalid slack token/cookie: {token}')

    def open_slack(self, menuitem: MenuItem):
        channel_id = menuitem.channel_id
        team_id = self.slack.team_id

        # don't allow escape from quoted string
        channel_id = channel_id.replace('"', '')
        team_id = team_id.replace('"', '')

        logger.info(f'open #{channel_id}')
        os.system(f'/usr/bin/open "slack://channel?team={team_id}&id={channel_id}"')

    def open_settings(self, menuitem: MenuItem):
        settings_window = rumps.Window(
            title='Slack Status Icon Settings',
            message='Enter Slack xoxs token or browser cookie:',
            ok='Save',
            cancel='Cancel',
            default_text=self.settings.token,
            dimensions=(400, 100),
        )
        settings_window.icon = APP_ICON
        settings_result = settings_window.run()
        if settings_result.clicked:
            self.settings.set_token(settings_result.text.strip())
            self.init_slack()

    @rumps.timer(1)
    def refresh_menu(self, _=None) -> None:
        now = time.time()
        if now - self.last_check < self.settings.update_interval:
            return
        self.last_check = now
        is_update_channels = False
        if now - self.last_check_channels > self.settings.channels_update_interval:
            self.last_check_channels = now
            is_update_channels = True

        logger.info(f'checking, full={is_update_channels}')
        count, unread = self.slack.check_unread(full_update=is_update_channels)
        logger.info(f'check result: {count}')

        menu = []
        for ch_id, ch_name, ch_count in unread:
            item_title = f'{ch_name} [{ch_count}]'
            menuitem = MenuItem(
                title=item_title,
                callback=self.open_slack,
                channel_id=ch_id,
            )
            menu.append(menuitem)

        self.menu.clear()
        self.icon = get_icon(count)
        self.menu = [*self.menu_items_header, None, *menu, None, *self.menu_items_footer]
