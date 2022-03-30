from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from popolo.models import Membership, WelshOnlyValidationError


@receiver(m2m_changed, sender=Membership.previous_party_affiliations.through)
def previous_party_affiliations(sender, **kwargs):
    """
    Raises a validation error if a previous party affiliation attempts
    to be added to a candidacy for a non-welse ballot. This is
    intended to be backup validation to stop us creating these
    relationships in our code or a terminal shell by mistake. We will
    use form validation to stop users adding these relationships.
    """
    if not kwargs["instance"].is_welsh_run_ballot:
        raise WelshOnlyValidationError()
