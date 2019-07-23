import os
import time

import rumps

from slack_api import Slack

DEFAULT_ICON = 'icons/slack.png'
UNREAD_CHECK_INTERVAL = 30
CHANNELS_LIST_UPDATE_INTERVAL = 20 * 60


def get_icon(count):
    if count <= 0:
        return DEFAULT_ICON
    if count < 10:
        return f'icons/slack{count}.png'
    return 'icons/slack_more.png'


class MenuBar(rumps.App):
    def __init__(self, slack_token):
        super(MenuBar, self).__init__('S', icon=DEFAULT_ICON, quit_button=None)
        self.slack = Slack(slack_token)
        self.full_check_last = time.time()

    def open_slack(self, menuitem):
        channel_id = menuitem.channel_id
        team_id = self.slack.team_id
        channel_id = channel_id.replace('"', '')
        team_id = team_id.replace('"', '')
        print(f'open #{channel_id}')
        os.system(f'/usr/bin/open "slack://channel?team={team_id}&id={channel_id}"')

    @rumps.timer(UNREAD_CHECK_INTERVAL)
    def refresh_menu(self, _=None) -> None:
        now = time.time()
        fast = True
        if now - self.full_check_last > CHANNELS_LIST_UPDATE_INTERVAL:
            fast = False
        print(f'checking, fast={fast}')
        count, unread = self.slack.check_unread_private(fast=fast)
        print(f'check result: {count}')

        menuitem_open = rumps.MenuItem(
            'Open', callback=self.open_slack, key='o',
        )
        menuitem_open.channel_id = ''
        menu = [menuitem_open, None]

        for ch_id, ch_name, ch_count in unread:
            item_title = f'{ch_name} [{ch_count}]'
            menuitem = rumps.MenuItem(
                title=item_title,
                callback=self.open_slack,
            )
            menuitem.channel_id = ch_id
            menu.append(menuitem)

        menu += [
            None,
            rumps.MenuItem('Quit', callback=rumps.quit_application, key='q')
        ]

        self.menu.clear()
        self.icon = get_icon(count)
        self.menu = menu

