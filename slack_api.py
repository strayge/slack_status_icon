from asyncio import Future
from typing import Union

import slack
from slack.web.slack_response import SlackResponse


class SlackWebClient(slack.WebClient):
    def client_boot(self, **kwargs) -> Union[Future, SlackResponse]:
        return self.api_call("client.boot", http_verb="GET", params=kwargs)

    def client_counts(self, **kwargs) -> Union[Future, SlackResponse]:
        return self.api_call("client.counts", http_verb="GET", params=kwargs)


class Slack:
    def __init__(self, token):
        self.slack = SlackWebClient(token=token)
        auth = self.check_auth()
        self._boot = None
        self._users = None
        if auth:
            self.team_id = auth.get('team_id')

    def check_auth(self):
        try:
            result = self.slack.auth_test().data
            if result.get('ok'):
                return result
        except Exception:
            return

    def check_unread_private(self, fast=False):
        if not self._boot or not fast:
            response = self.slack.client_boot()
            if response.get('ok'):
                self._boot = response
                print('client_boot ok')
            response = self.slack.users_list()
            if response.get('ok'):
                self._users = response
                print('users_list ok')
        counts = self.slack.client_counts()

        unread_channels = []
        total_unread = 0

        if not counts.get('ok'):
            return total_unread, unread_channels

        threads_u = counts.get('threads', {}).get('has_unreads', False)
        threads_m = counts.get('threads', {}).get('mention_count', 0)
        total = max(int(threads_u), threads_m)
        total_unread += total

        for channel in counts.get('channels', []):
            channel_id = channel.get('id')
            unread = channel.get('has_unreads', False)
            mentions = channel.get('mention_count', 0)
            total = max(int(unread), mentions)

            channel_name = channel_id
            for ch in (
                    self._boot.get('channels',[]) + self._boot.get('groups',[])
            ):
                if ch.get('id') == channel_id:
                    channel_name = ch.get('name', channel_id)
                    break

            if total:
                unread_channels.append([channel_id, channel_name, total])

            if channel_id not in self._boot.get('self', {}).get('prefs', {}).get('muted_channels', '').split(','):
                total_unread += total

        for im in counts.get('ims', []):
            channel_id = im.get('id')
            unread = im.get('has_unreads', False)
            mentions = im.get('mention_count', 0)
            total = max(int(unread), mentions)

            user_id = None
            for boot_im in self._boot.get('ims'):
                if channel_id == boot_im.get('id'):
                    user_id = boot_im.get('user')
                    break
            username = None
            if user_id:
                for user in self._users.get('members', []):
                    if user.get('id') == user_id:
                        username = user.get('real_name', user_id)
                        break

            if not username:
                username = channel_id
            channel_name = f'IM: {username}'
            if total:
                unread_channels.append([channel_id, channel_name, total])
            total_unread += total

        for mpim in counts.get('mpims', []):
            channel_id = mpim.get('id')
            unread = mpim.get('has_unreads', False)
            mentions = mpim.get('mention_count', 0)
            total = max(int(unread), mentions)
            channel_name = f'MPIM #{channel_id}'
            if total:
                unread_channels.append([channel_id, channel_name, total])
            total_unread += total

        return total_unread, unread_channels

    # def get_channels(self, fast):
    #     public_channels = self.slack.channels_list().data.get('channels', [])
    #     my_public_channels = [c for c in public_channels if c.get('is_member')]
    #     private_channels = self.slack.groups_list().data.get('groups', [])
    #     ims = []
    #     group_ims = []
    #
    #     if not fast:
    #         ims = self.slack.im_list().data.get('ims', [])
    #         group_ims = self.slack.mpim_list().data.get('groups', [])
    #
    #     return [*my_public_channels, *private_channels, *ims, *group_ims]

    # def check_unread_public(self, fast=False):
    #     unread = []
    #     total_count = 0
    #     channels = self.get_channels(fast=fast)
    #     for channel in channels:
    #         sleep(0.2)
    #         channel_id = channel.get('id')
    #         channel_name = channel.get('name')
    #         if not channel_name:
    #             channel_name = '@' + channel.get('user')
    #         if channel.get('is_channel'):
    #             response = self.slack.channels_info(
    #                 channel=channel_id
    #             ).data.get('channel')
    #         elif channel.get('is_group'):
    #             response = self.slack.groups_info(
    #                 channel=channel_id
    #             ).data.get('group')
    #         elif channel.get('is_im'):
    #             response = self.slack.conversations_info(
    #                 channel=channel_id
    #             ).data.get('channel')
    #         else:
    #             response = {}
    #         unread_count = 0
    #         if channel_name not in BLACKLISTED_NAMES:
    #             unread_count = response.get('unread_count_display')
    #         if unread_count:
    #             total_count += unread_count
    #             unread.append([channel_id, channel_name, unread_count])
    #
    #     return total_count, unread

