import textwrap
from urllib.parse import urljoin

from django.conf import settings
from utils.mail import send_mail


def get_name_change_notification_message(
    person, prev_name, new_name, ballots, username
):
    person_url = urljoin(settings.BASE_URL, person.get_absolute_url())

    prefix = ""
    if settings.DC_ENVIRONMENT not in ["production", "testing"]:
        prefix = f"This email was sent from the {settings.DC_ENVIRONMENT.upper()} environment.\n\n"

    message = textwrap.dedent(
        f"""\
        {prefix}Hello,
        
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
    prefix = ""
    if settings.DC_ENVIRONMENT not in ["production", "testing"]:
        prefix = f"[{settings.DC_ENVIRONMENT.upper()}] "
    subject = f"{prefix}Name for candidate updated"

    return send_mail(
        subject,
        get_name_change_notification_message(
            person, prev_name, new_name, ballots, username
        ),
        settings.SOPN_UPDATE_NOTIFICATION_EMAILS,
    )
