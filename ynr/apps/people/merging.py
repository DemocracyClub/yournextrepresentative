import json

from django.conf import settings
from django.contrib.admin.utils import NestedObjects
from django.db import IntegrityError, connection, transaction

from candidates.models import (
    LoggedAction,
    PersonRedirect,
    UnsafeToDelete,
    merge_popit_people,
)
from candidates.models.versions import get_person_as_version_data
from candidates.views.version_data import get_change_metadata, get_client_ip


class InvalidMergeError(ValueError):
    """
    Raised when merging two people would cause invalid data or some other
    oddness
    """

    pass


class PersonMerger:
    """
    Deals with merging two people, ensuring that no data is lost
    """

    def __init__(self, dest_person, source_person, request=None):
        self.dest_person = dest_person
        self.source_person = source_person
        self.request = request

    def safe_delete(self, model):
        collector = NestedObjects(using=connection.cursor().db.alias)
        collector.collect([model])

        if len(collector.nested()) > 1:
            related_objects = "\n\t".join(
                [repr(m) for m in collector.nested()[1]]
            )
            raise UnsafeToDelete(
                "Can't delete '{}' with related objects: \n {}".format(
                    model, related_objects
                )
            )

        return model.delete()

    def merge_versions_json(self):
        # Merge the reduced JSON representations:
        merge_popit_people(
            get_person_as_version_data(self.dest_person),
            get_person_as_version_data(self.source_person),
        )

        # Make sure the secondary person's version history is appended, so it
        # isn't lost.
        dest_person_versions = json.loads(self.dest_person.versions)
        dest_person_versions += json.loads(self.source_person.versions)
        self.dest_person.versions = json.dumps(dest_person_versions)

    def merge_person_attrs(self):
        """
        Merge attributes on Person from source in to dest
        """

        for field in settings.SIMPLE_POPOLO_FIELDS:
            source_value = getattr(self.source_person, field.name, None)
            dest_value = getattr(self.dest_person, field.name, None)
            # Assume we want to keep the value from dest_person
            if not dest_value:
                setattr(self.dest_person, field.name, source_value)

            # Special case "name"
            if field.name == "name":
                if source_value != dest_value:
                    self.dest_person.other_names.update_or_create(
                        name=source_value
                    )

    def merge_images(self):
        # Change the secondary person's images to point at the primary
        # person instead:
        existing_primary_image = self.dest_person.images.filter(
            is_primary=True
        ).exists()

        self.source_person.images.update(
            is_primary=False, person=self.dest_person
        )

    def merge_logged_actions(self):
        self.source_person.loggedaction_set.update(person=self.dest_person)

    def deep_merge_related_membership_objects(self, msource, mdest):
        """
        This method should update all related objects on msource, to point to
        mdest. This only happens when two Memberships with
        (Person ID, Ballot Paper) would exist when merging two people. This
        case shoudl be very rare, as it would only happen when the same person
        got added twice to the same ballot, just with duplicate Person models.

        We should be able to safely delete msource at the end of this method.

        Assume that the non-related field data on mdest is the correct data,
        e.g `party_list_position`.

        Also assume that `Party` is "more correct" in mdest.
        """
        if hasattr(msource, "result"):
            if hasattr(mdest, "result"):
                raise ValueError("Trying to merge two Memberships with results")
            else:
                msource.result.membership = mdest
                mdest.result.save()

        self.safe_delete(msource)

    def merge_memberships(self):
        for membership in self.source_person.memberships.all():
            existing_membership_qs = self.dest_person.memberships.filter(
                post_election=membership.post_election
            )
            if existing_membership_qs.exists():
                # This is a duplicate membership, so we need to merge the
                # related objects
                self.deep_merge_related_membership_objects(
                    membership, existing_membership_qs.get()
                )
            else:
                membership.person = self.dest_person
                membership.save()
        # Check that we've not causes duplicate (membership, election) pairs.
        # We need to do this manually because we can't add a DB constraint
        # spanning the three tables (Membership->Ballot->Election)
        person_elections = {
            mem.post_election.election_id
            for mem in self.dest_person.memberships.select_related(
                "post_election"
            )
        }
        if len(person_elections) != self.dest_person.memberships.count():
            raise InvalidMergeError(
                "Merging would cause this person to be standing more than once in the same election"
            )

    def setup_redirect(self):
        # Create a redirect from the old person to the new person:
        PersonRedirect.objects.create(
            old_person_id=self.source_person.pk,
            new_person_id=self.dest_person.pk,
        )

    def merge(self, delete=True):
        """
        Do everything we need in order to merge two people.

        At the end of this, `self.source_person` should have no related objects
        left, as checked by `self.check_safe_to_delete()`
        """
        with transaction.atomic():
            # Merge all the things
            self.merge_person_attrs()
            self.merge_versions_json()
            self.merge_images()
            self.merge_logged_actions()
            self.merge_memberships()

            # Save the dest person (don't assume the methods above do this)

            # TODO: Deal with change metadata
            # self.dest_person.record_version(change_metadata)
            self.dest_person.save()

            # Post merging tasks
            self.setup_redirect()
            if delete:
                # Delete the old person
                self.safe_delete(self.source_person)

            change_metadata = get_change_metadata(
                self.request,
                "After merging person {}".format(self.source_person.pk),
            )

            # Log that the merge has taken place, and will be shown in
            # the recent changes, leaderboards, etc.
            if self.request:
                LoggedAction.objects.create(
                    user=self.request.user,
                    action_type="person-merge",
                    ip_address=get_client_ip(self.request),
                    popit_person_new_version=change_metadata["version_id"],
                    person=self.dest_person,
                    source=change_metadata["information_source"],
                )
