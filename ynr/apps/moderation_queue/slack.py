from django.conf import settings
from celery import shared_task

from utils.slack import SlackHelper
import json


class FlaggedEditSlackPoster:
    def __init__(self, logged_action):
        self.sh = SlackHelper()
        self.logged_action = logged_action

    def _dict_to_kv_format(self, data, indent=1):
        if not data:
            return None
        out = []
        if isinstance(data, str):
            return data
        if isinstance(data, list):
            for item in data:
                out.append(self._dict_to_kv_format(item))
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, dict):
                    for kk, vv in v.items():
                        if not vv:
                            del kk[vv]
                    if v:
                        v = self._dict_to_kv_format(v, indent + 1)
                tabs = "\t" * indent
                if v:
                    out.append(
                        "{tabs}*{label}*:\n{tabs}\t{value}".format(
                            tabs=tabs, label=k, value=v
                        )
                    )
        return "\n".join(out)

    def format_text(self, diff):
        path = diff["path"]
        default_text = "*{path}*:\n{value}"

        if path.startswith("other_names"):
            path = "Other Name"
        else:
            path = path.replace("_", " ").replace("/", " -> ")

        value = diff.get("value", diff.get("previous_value"))
        value = self._dict_to_kv_format(value)
        if value:
            value = value.replace("was known to be ", " ")
        if diff["op"] == "replace":
            value = "{} \n *previously:*\n{}\n---------".format(
                value, diff["previous_value"]
            )

        text = default_text.format(path=path, value=value)
        return text

    def format_message(self):
        message_divider = {"type": "divider"}

        header_text = """
*{flagged_reason}*\n\n

{username} edited <https://candidates.democracyclub.org.uk{candidate_url}|{candidate_name}>\n
with the source: \n> {source}
""".format(
            flagged_reason=self.logged_action.flagged_reason,
            username=self.logged_action.user.username,
            candidate_url=self.logged_action.person.get_absolute_url(),
            candidate_name=self.logged_action.person.name,
            source=self.logged_action.source,
        )

        image_url = None
        if self.logged_action.person.primary_image:
            image_url = self.logged_action.person.primary_image.url
            if not image_url.startswith("http"):
                image_url = None

        message_header = {
            "type": "section",
            "text": {"type": "mrkdwn", "text": header_text},
        }
        if image_url:
            message_header["accessory"] = {
                "type": "image",
                "image_url": image_url,
                "alt_text": "Photo of {}".format(
                    self.logged_action.person.name
                ),
            }

        message_added_fields = []
        message_removed_fields = []
        message_replaced_fields = []
        for diff in self.logged_action.person.version_diffs[0]["diffs"][0][
            "parent_diff"
        ]:

            section_category = None
            text = self.format_text(diff)
            if not text:
                continue

            if diff["op"] == "add":
                section_category = message_added_fields

            if diff["op"] == "remove":
                section_category = message_removed_fields

            if diff["op"] == "replace":
                section_category = message_replaced_fields

            section = {
                "type": "section",
                "fields": [{"type": "mrkdwn", "text": text}],
            }
            section_category.append(section)

        message_added_header = {
            "type": "section",
            "text": {"type": "mrkdwn", "text": ":heavy_plus_sign: *Added*:"},
        }

        message_removed_header = {
            "type": "section",
            "text": {"type": "mrkdwn", "text": ":x: *Removed*:"},
        }

        message_replace_header = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":arrows_counterclockwise: *Replaced*:",
            },
        }

        message = [message_divider]
        message.append(message_header)
        if message_added_fields:
            message.append(message_divider)
            message.append(message_added_header)
            message.extend(message_added_fields)
        if message_replaced_fields:
            message.append(message_divider)
            message.append(message_replace_header)
            message.extend(message_replaced_fields)
        if message_removed_fields:
            message.append(message_divider)
            message.append(message_removed_header)
            message.extend(message_removed_fields)
        # message.extend([message_divider, message_buttons])
        self.message = json.dumps(message)
        return self.message

    def post_message(self):
        self.sh.client.chat.post_message(
            "C59LHLH7A",
            text="Edit to {}".format(self.logged_action.person.name),
            blocks=self.message,
            username=settings.CANDIDATE_BOT_USERNAME,
            icon_emoji=":robot_face:",
        )


class FlaggedEditSlackReplyer:
    def __init__(self, payload):
        self.payload = payload
        self.sh = SlackHelper()

    def reply(self):
        self.sh.client.chat.update(
            self.payload["channel"]["id"],
            self.payload["message_ts"],
            text="Message updated",
            attachments=[
                {
                    "text": "Edit approved by @{}".format(
                        self.payload["user"]["name"]
                    )
                }
            ],
        )


@shared_task
def post_action_to_slack(pk):
    if getattr(settings, "RUNNING_TESTS", False):
        # Never do anything when we're running tests
        return

    from candidates.models import LoggedAction

    la = LoggedAction.objects.get(pk=pk)
    slack_helper = FlaggedEditSlackPoster(la)
    slack_helper.format_message()
    slack_helper.post_message()
