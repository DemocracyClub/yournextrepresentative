from django.db.models.signals import post_delete
from django.dispatch import receiver

from people.models import Person
from candidates.models import LoggedAction
from candidates.models.db import ActionType


@receiver(post_delete, sender=Person)
def created_logged_action(sender, **kwargs):
    """
    Creates a LoggedAction to keep a record of person that get deleted unless
    one already exists for this person
    """
    LoggedAction.objects.get_or_create(
        action_type=ActionType.PERSON_DELETE, person_pk=kwargs["instance"].pk
    )
