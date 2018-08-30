from popolo.models import Membership, Person

from candidates.models import LoggedAction, raise_if_unsafe_to_delete
from candidates.models.auth import check_creation_allowed
from candidates.views.version_data import get_change_metadata, get_client_ip
from tasks.models import pause_task_signal


@pause_task_signal
def add_person(request, person_data):
    person = Person.objects.create(name=person_data["name"])

    change_metadata = get_change_metadata(request, person_data["source"])

    person.record_version(change_metadata, new_person=True)
    person.save()

    LoggedAction.objects.create(
        user=request.user,
        person=person,
        action_type="person-create",
        ip_address=get_client_ip(request),
        popit_person_new_version=change_metadata["version_id"],
        source=change_metadata["information_source"],
    )
    return person


@pause_task_signal
def update_person(
    request=None, person=None, party=None, post_election=None, source=None
):
    election = post_election.election

    person.not_standing.remove(election)

    check_creation_allowed(request.user, person.current_candidacies)

    membership, _ = Membership.objects.update_or_create(
        post=post_election.post,
        person=person,
        role=election.candidate_membership_role,
        post_election=post_election,
        defaults={
            "on_behalf_of": party,
            "party_list_position": None,
            "elected": None,
        },
    )

    # Now remove other memberships in this election for that
    # person, although we raise an exception if there is any
    # object that has a
    # ForeignKey to the membership, since that would result in
    # losing data.
    old_memberships = Membership.objects.exclude(pk=membership.pk).filter(
        person=person,
        post_election=post_election,
        role=election.candidate_membership_role,
    )
    for old_membership in old_memberships:
        raise_if_unsafe_to_delete(old_membership)
        old_membership.delete()

    change_metadata = get_change_metadata(request, source)

    person.record_version(change_metadata)
    person.save()

    LoggedAction.objects.create(
        user=request.user,
        person=person,
        action_type="person-update",
        ip_address=get_client_ip(request),
        popit_person_new_version=change_metadata["version_id"],
        source=change_metadata["information_source"],
    )
