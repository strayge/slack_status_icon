import logging
from asyncio import Future
from typing import Union

import slack
from slack.web.slack_response import SlackResponse

logger = logging.getLogger(__name__)


class SlackWebClient(slack.WebClient):
    """
    Introduced non-documented methods for getting info about all channels/members in single call
    """

    def client_boot(self, **kwargs) -> Union[Future, SlackResponse]:
        return self.api_call("client.boot", http_verb="GET", params=kwargs)

    def client_counts(self, **kwargs) -> Union[Future, SlackResponse]:
        return self.api_call("client.counts", http_verb="GET", params=kwargs)


class Slack:
    def __init__(self, token: str):
        self.slack = SlackWebClient(token=token)

        # cache heavy calls
        self._info = None
        self._users = None

        self.team_id = None
        auth = self.check_auth()
        if auth:
            self.team_id = auth.get('team_id')

    def check_auth(self):
        try:
            result = self.slack.auth_test().data
            if result.get('ok'):
                return result
        except Exception:
            return

    def _full_update(self):
        response = self.slack.client_boot()
        if response.get('ok'):
            self._info = response
            logger.info('client.boot ok')
        response = self.slack.users_list()
        if response.get('ok'):
            self._users = response
            logger.info('users.list ok')

    def _count_unread_from_channel(self, channel: dict) -> int:
        """
        Returns counts of mentions in channel or 1 for unread mark
        """
        unread_mark = channel.get('has_unreads', False)
        mentions = channel.get('mention_count', 0)
        return max(int(unread_mark), mentions)

    def _get_channel_name_by_id(self, channel_id: str) -> str:
        known_channels = self._info.get('channels', []) + self._info.get('groups', [])
        for ch in known_channels:
            if ch.get('id') == channel_id:
                return ch.get('name', channel_id)
        return channel_id

    def _is_channel_muted(self, channel_id: str) -> bool:
        muted_channels = self._info.get('self', {}).get('prefs', {}).get('muted_channels', '').split(',')
        return channel_id in muted_channels

    def _get_username_by_im_id(self, im_id: str) -> str:
        default_username = f'#{im_id}'
        user_id = None
        for im in self._info.get('ims', []):
            if im_id == im.get('id'):
                user_id = im.get('user')
                break
        for user in self._users.get('members', []):
            if user.get('id') == user_id:
                return user.get('real_name', default_username)
        return default_username

    def check_unread(self, full_update: bool = False):
        if not self._info or full_update:
            self._full_update()

        unread_by_channel = []
        total_unread_count = 0

        counts = self.slack.client_counts()
        if not counts.get('ok'):
            logger.warning('client.counts returned non-ok')
            return total_unread_count, unread_by_channel

        threads = counts.get('threads', {})
        channels = counts.get('channels', [])
        ims = counts.get('ims', [])
        multipeople_ims = counts.get('mpims', [])

        threads_count = self._count_unread_from_channel(threads)
        if threads_count:
            unread_by_channel.append(['', 'Threads', threads_count])
            total_unread_count += threads_count

        for channel in channels:
            unread_count = self._count_unread_from_channel(channel)
            channel_id = channel.get('id')
            channel_name = self._get_channel_name_by_id(channel_id)
            if unread_count:
                unread_by_channel.append([channel_id, channel_name, unread_count])
                if not self._is_channel_muted(channel_id):
                    total_unread_count += unread_count

        for im in ims:
            unread_count = self._count_unread_from_channel(im)
            channel_id = im.get('id')
            username = self._get_username_by_im_id(channel_id)
            if unread_count:
                unread_by_channel.append([channel_id, username, unread_count])
                total_unread_count += unread_count

        for mpim in multipeople_ims:
            unread_count = self._count_unread_from_channel(mpim)
            channel_id = mpim.get('id')
            channel_name = f'#{channel_id}'
            if unread_count:
                unread_by_channel.append([channel_id, channel_name, unread_count])
                total_unread_count += unread_count

        return total_unread_count, unread_by_channel
