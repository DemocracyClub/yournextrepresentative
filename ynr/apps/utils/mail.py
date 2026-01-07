from django.conf import settings
from django.core.mail import send_mail as dj_send_mail
from django_q.tasks import async_task


def send_mail(subject, message, recipients):
    return async_task(
        dj_send_mail,
        # send_mail args
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipients,
        fail_silently=False,
        # django q2 args
        timeout=15,
    )
