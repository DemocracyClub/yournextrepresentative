import textwrap

from django.conf import settings
from utils.mail import send_mail

from .models import BallotSOPN


def send_ballot_sopn_update_notification(ballot_sopn: BallotSOPN, request):
    message_prefix = ""
    if settings.DC_ENVIRONMENT not in ["production", "testing"]:
        message_prefix = f"This email was sent from the {settings.DC_ENVIRONMENT.upper()} environment.\n\n"

    message = textwrap.dedent(
        f"""\
    {message_prefix}Hello,
    
    The user {request.user.username} has updated the SOPN for the ballot with ID {ballot_sopn.ballot.ballot_paper_id}.
    
    You can see this newly uploaded SOPN here:
    
    {request.build_absolute_uri(ballot_sopn.get_absolute_url())}
    
    Their reason for the new upload was:
    
    > "{ballot_sopn.replacement_reason}"
    
    """
    )

    subject_prefix = ""
    if settings.DC_ENVIRONMENT not in ["production", "testing"]:
        subject_prefix = f"[{settings.DC_ENVIRONMENT.upper()}] "
    subject = (
        f"{subject_prefix}SOPN for {ballot_sopn.ballot.ballot_paper_id} updated"
    )

    send_mail(
        subject,
        message,
        settings.SOPN_UPDATE_NOTIFICATION_EMAILS,
    )
