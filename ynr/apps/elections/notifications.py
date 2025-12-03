import textwrap
from urllib.parse import urljoin

from django.conf import settings
from utils.mail import send_mail


def get_ballot_lock_notification_message(ballot, username):
    return textwrap.dedent(
        f"""\
        Hello,
        
        The user {username} re-locked the ballot {ballot.ballot_paper_id}.
        
        You can see a history of changes to this ballot at
        {urljoin(settings.BASE_URL, ballot.get_absolute_url())}#history
        """
    )


def send_ballot_lock_notification(ballot, username):
    return send_mail(
        "Ballot re-locked",
        get_ballot_lock_notification_message(ballot, username),
        settings.SOPN_UPDATE_NOTIFICATION_EMAILS,
    )
