import textwrap
from urllib.parse import urljoin

from django.conf import settings
from utils.mail import send_mail


def get_ballot_lock_notification_message(ballot, username):
    prefix = ""
    if settings.DC_ENVIRONMENT not in ["production", "testing"]:
        prefix = f"This email was sent from the {settings.DC_ENVIRONMENT.upper()} environment.\n\n"
    return textwrap.dedent(
        f"""\
        {prefix}Hello,
        
        The user {username} re-locked the ballot {ballot.ballot_paper_id}.
        
        You can see a history of changes to this ballot at
        {urljoin(settings.BASE_URL, ballot.get_absolute_url())}#history
        """
    )


def send_ballot_lock_notification(ballot, username):
    prefix = ""
    if settings.DC_ENVIRONMENT not in ["production", "testing"]:
        prefix = f"[{settings.DC_ENVIRONMENT.upper()}] "
    subject = f"{prefix}Ballot re-locked"

    return send_mail(
        subject,
        get_ballot_lock_notification_message(ballot, username),
        settings.SOPN_UPDATE_NOTIFICATION_EMAILS,
    )
