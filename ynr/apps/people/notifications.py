import textwrap
from urllib.parse import urljoin

from django.conf import settings
from utils.mail import send_mail


def get_name_change_notification_message(
    person, prev_name, new_name, ballots, username
):
    person_url = urljoin(settings.BASE_URL, person.get_absolute_url())
    message = textwrap.dedent(
        f"""\
        Hello,
        
        The user {username} changed the name of {person_url} from {prev_name} to {new_name}.
        
        This candidate is currently standing in the following ballots:
        """
    )
    for ballot in ballots:
        message = (
            message
            + f"- {urljoin(settings.BASE_URL, ballot.get_absolute_url())}\n"
        )
    return message


def send_name_change_notification(
    person, prev_name, new_name, ballots, username
):
    return send_mail(
        "Name for candidate updated",
        get_name_change_notification_message(
            person, prev_name, new_name, ballots, username
        ),
        settings.SOPN_UPDATE_NOTIFICATION_EMAILS,
    )
