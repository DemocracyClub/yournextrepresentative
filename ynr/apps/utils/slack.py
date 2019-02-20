from slacker import Slacker

from django.conf import settings


class SlackHelper:
    def __init__(self, user=settings.CANDIDATE_BOT_USERNAME):
        self.client = Slacker(settings.SLACK_TOKEN)
        self.user = user

    def post_message(self, to, message_text, attachments=None, extra_dict=None):
        kwargs = {
            "username": self.user,
            "icon_emoji": ":robot_face:",
            "text": message_text,
            "attachments": attachments,
        }
        if extra_dict:
            kwargs.update(extra_dict)
        self.client.chat.post_message(to, **kwargs)
