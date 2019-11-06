import re
from collections import defaultdict
from datetime import datetime

from django.conf import settings
from django.db.models.query import prefetch_related_objects

from parties.models import Party
from ynr_refactoring.settings import PersonIdentifierFields

# FIXME: check all the preserve_fields are dealt with


def get_person_as_version_data(person, new_person=False):
    """
    If new_person is True then skip some DB checks that we know will be
    empty. This should reduce the number of queries needed.
    """

    # Prefetch to reduce the number of queries
    prefetch_related_objects([person], "tmp_person_identifiers")

    from candidates.election_specific import shorten_post_label

    result = {}
    result["id"] = str(person.id)

    # Add PersonIdentifier fields in to the global version namespace
    # TODO: move these to dict to make it easier to merge/split/revert
    existing_identifiers = {
        identifier.value_type: identifier.value
        for identifier in person.tmp_person_identifiers.all()
    }
    for field in PersonIdentifierFields:
        result[field.name] = existing_identifiers.get(field.name, "")

    for field in settings.SIMPLE_POPOLO_FIELDS:
        result[field.name] = getattr(person, field.name) or ""

    # Add legacy identifiers
    # TODO: these should use the PersonIdenfitiers model and value types,
    # but this code emulates the legacy way of adding IDs.
    if person.get_single_identifier_of_type("theyworkforyou"):
        result["identifiers"] = []
        new_id = person.get_single_identifier_of_type(
            "theyworkforyou"
        ).internal_identifier
        if "publicwhip" not in new_id:
            new_id = "uk.org.publicwhip/person/{}".format(new_id)

        result["identifiers"].append(
            {"identifier": new_id, "scheme": "uk.org.publicwhip"}
        )
    if person.get_single_identifier_of_type("twitter_username"):
        result["identifiers"] = result.get("identifiers", [])
        result["identifiers"].append(
            {
                "identifier": person.get_single_identifier_of_type(
                    "twitter_username"
                ).internal_identifier,
                "scheme": "twitter",
            }
        )

    extra_values = {}
    result["other_names"] = []
    standing_in = {}
    party_memberships = {}

    if not new_person:
        result["other_names"] = [
            {
                "name": on.name,
                "note": on.note,
                "start_date": on.start_date,
                "end_date": on.end_date,
            }
            for on in person.other_names.order_by(
                "name", "start_date", "end_date"
            )
        ]

        for membership in person.memberships.filter(post__isnull=False):
            post = membership.post
            ballot = membership.ballot
            election = ballot.election
            standing_in[ballot.election.slug] = {
                "post_id": post.slug,
                "name": shorten_post_label(post.label),
            }
            if membership.elected is not None:
                standing_in[election.slug]["elected"] = membership.elected
            if membership.party_list_position is not None:
                standing_in[election.slug][
                    "party_list_position"
                ] = membership.party_list_position
            party = membership.party
            party_memberships[ballot.election.slug] = {
                "id": party.legacy_slug,
                "name": party.name,
            }
        for not_standing_in_election in person.not_standing.all():
            standing_in[not_standing_in_election.slug] = None
            # Delete party memberships if not standing in this election
            party_memberships.pop(not_standing_in_election.slug, None)

    # Add `favourite_biscuits` to an `extra_fields` key
    # to re-produce the previous ExtraField model.
    # This is done like this to save changing the version diff
    # for exery edit to move to key to the parent object.
    # In the future we will have to run a script to move all the
    # keys to wherever we want them.
    extra_fields = {"favourite_biscuits": person.favourite_biscuit or ""}

    result["extra_fields"] = extra_fields

    result["standing_in"] = standing_in
    result["party_memberships"] = party_memberships
    return result


def revert_person_from_version_data(person, version_data):

    from popolo.models import Membership, Post
    from candidates.models import raise_if_unsafe_to_delete

    from elections.models import Election

    for field in settings.SIMPLE_POPOLO_FIELDS:
        new_value = version_data.get(field.name)
        if new_value:
            setattr(person, field.name, new_value)
        else:
            setattr(person, field.name, "")

    # Remove old PersonIdentifier objects
    from people.models import PersonIdentifier

    PersonIdentifier.objects.filter(
        person=person
    ).editable_value_types().delete()

    # Add PersonIdentifier objects we want back again
    # TODO: https://github.com/DemocracyClub/yournextrepresentative/issues/697
    for field in PersonIdentifierFields:
        new_value = version_data.get(field.name, "")
        if new_value:
            PersonIdentifier.objects.update_or_create(
                person=person, value=new_value, value_type=field.name
            )

    # Remove all other names, and recreate:
    person.other_names.all().delete()
    for on in version_data.get("other_names", []):
        person.other_names.create(
            name=on["name"],
            note=on.get("note", ""),
            start_date=on.get("start_date"),
            end_date=on.get("end_date"),
        )

    # Remove all candidacies, and recreate:
    qs = (
        Membership.objects.filter(person=person)
        .filter(result=None)
        .filter(ballot__candidates_locked=False)
    )
    for membership in qs:
        raise_if_unsafe_to_delete(membership)
        membership.delete()
    # Also remove the indications of elections that this person is
    # known not to be standing in:
    person.not_standing.clear()
    for election_slug, standing_in in version_data["standing_in"].items():
        election = Election.objects.get(slug=election_slug)
        # If the value for that election slug is None, then that means
        # the person is known not to be standing:
        if standing_in is None:
            person.not_standing.add(election)
        else:
            # Get the corresponding party membership data:
            party = Party.objects.get(
                legacy_slug=version_data["party_memberships"][election_slug][
                    "id"
                ]
            )
            post = Post.objects.get(slug=standing_in["post_id"])
            Membership.objects.create(
                party=party,
                person=person,
                post=post,
                elected=standing_in.get("elected"),
                party_list_position=standing_in.get("party_list_position"),
                ballot=election.ballot_set.get(post=post),
            )

    person.save()


def version_timestamp_key(version):
    return datetime.strptime(version["timestamp"], "%Y-%m-%dT%H:%M:%S.%f")


def is_a_merge(version):
    m = re.search(r"^After merging person (\d+)", version["information_source"])
    if m:
        return m.group(1)
    return None


def get_versions_parent_map(versions_data):
    version_id_to_parent_ids = {}
    if not versions_data:
        return version_id_to_parent_ids
    canonical_person_id = versions_data[0]["data"]["id"]
    ordered_versions = sorted(versions_data, key=version_timestamp_key)
    person_id_to_ordered_versions = defaultdict(list)
    # Divide all the version with the same ID into separate ordered
    # lists, and record the parent of each version that we get from
    # doing that:
    for version in ordered_versions:
        version_id = version["version_id"]
        person_id = version["data"]["id"]
        versions_for_person_id = person_id_to_ordered_versions[person_id]
        if versions_for_person_id:
            last_version_id = versions_for_person_id[-1]["version_id"]
            version_id_to_parent_ids[version_id] = [last_version_id]
        else:
            version_id_to_parent_ids[version_id] = []
        versions_for_person_id.append(version)
    # Now go through looking for versions that represent merges. Note
    # that it's *possible* for someone to create a new version that
    # doesn't represent a merge but which has a information_source
    # message that makes it look like one. We try to raise an
    # exception if this might have happened, by checking that (a) the
    # person ID in the message also has history in this versions array
    # and (b) the number of unique person IDs in the versions is one
    # more than the number of versions that look like merges. We raise
    # an exception in either of these situations.
    number_of_person_ids = len(person_id_to_ordered_versions.keys())
    number_of_merges = 0
    for version in ordered_versions:
        version_id = version["version_id"]
        merged_from = is_a_merge(version)
        if merged_from is None:
            continue
        if merged_from not in person_id_to_ordered_versions:
            # This can happen because for some time there was a bug
            # where the history of the secondary person wasn't
            # included on merging; just treat this as any other
            # version in that case.
            continue
        number_of_merges += 1
        last_version_id_of_other = person_id_to_ordered_versions[merged_from][
            -1
        ]["version_id"]
        version_id_to_parent_ids[version_id].append(last_version_id_of_other)
    if (number_of_merges + 1) != number_of_person_ids:
        msg = (
            "It looks like there was a bogus merge version for person "
            "with ID {person_id}; there were {nm} merge versions and {np} "
            "person IDs."
        )
        raise Exception(
            msg.format(
                person_id=canonical_person_id,
                nm=number_of_merges,
                np=number_of_person_ids,
            )
        )
    return version_id_to_parent_ids
