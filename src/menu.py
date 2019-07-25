import logging
import os
import time

import rumps

from slack_api import Slack

DEFAULT_ICON = 'icons/slack.png'
UNREAD_CHECK_INTERVAL = 10
CHANNELS_LIST_UPDATE_INTERVAL = 20 * 60

logger = logging.getLogger(__name__)


def get_icon(count: int) -> str:
    if count <= 0:
        return DEFAULT_ICON
    if count < 10:
        return f'icons/slack{count}.png'
    return 'icons/slack_more.png'


class Menu(rumps.App):
    def __init__(self, slack_token: str):
        super().__init__('Slack', icon=DEFAULT_ICON, quit_button=None)
        self.slack = Slack(slack_token)
        self.full_check_last = time.time()

        menuitem_open = rumps.MenuItem('Open', callback=self.open_slack, key='o')
        menuitem_open.channel_id = ''
        menuitem_quit = rumps.MenuItem('Quit', callback=rumps.quit_application, key='q')
        self.menu_items_header = [menuitem_open]
        self.menu_items_footer = [menuitem_quit]

    def open_slack(self, menuitem: rumps.MenuItem):
        channel_id = menuitem.channel_id
        team_id = self.slack.team_id
        channel_id = channel_id.replace('"', '')
        team_id = team_id.replace('"', '')
        logger.info(f'open #{channel_id}')
        os.system(f'/usr/bin/open "slack://channel?team={team_id}&id={channel_id}"')

    @rumps.timer(UNREAD_CHECK_INTERVAL)
    def refresh_menu(self, _=None) -> None:
        now = time.time()
        full = True
        if now - self.full_check_last > CHANNELS_LIST_UPDATE_INTERVAL:
            full = False
        logger.info(f'checking, full={full}')
        count, unread = self.slack.check_unread(full_update=full)
        logger.info(f'check result: {count}')

        menu = []
        for ch_id, ch_name, ch_count in unread:
            item_title = f'{ch_name} [{ch_count}]'
            menuitem = rumps.MenuItem(
                title=item_title,
                callback=self.open_slack,
            )
            menuitem.channel_id = ch_id
            menu.append(menuitem)

        self.menu.clear()
        self.icon = get_icon(count)
        self.menu = [*self.menu_items_header, None, *menu, None, *self.menu_items_footer]
