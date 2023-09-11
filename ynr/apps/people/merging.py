import contextlib
from collections import OrderedDict

from candidates.models import (
    LoggedAction,
    PersonRedirect,
    UnsafeToDelete,
    merge_popit_people,
)
from candidates.models.db import ActionType
from candidates.models.versions import get_person_as_version_data
from candidates.views.version_data import get_change_metadata, get_client_ip
from django.conf import settings
from django.contrib.admin.utils import NestedObjects
from django.db import connection, transaction
from duplicates.merge_helpers import alter_duplicate_suggestion_post_merge
from people.models import PersonImage
from results.models import ResultEvent


class InvalidMergeError(ValueError):
    """
    Raised when merging two people would cause invalid data or some other
    oddness
    """


class PersonMerger:
    """
    Deals with merging two people, ensuring that no data is lost.

    We always merge higher IDs _into_ lower IDs. That is, when merging person
    3 and person 4, this class will move everything on person 4 to person 3 and
    delete person 4.

    We prefer lower IDs because they help maintain ID stability over time –
    older IDs will have existed for longer so the chance someone else is using
    it in their own data or in a URL is higher.

    The lower ID is assigned to `self.dest_person` and the lower ID
    `self.source_person`.

    The properties and related models of `source_person` are added to
    `dest_person` and `source_person` is deleted, checking no remaining related
    models exist.

    In the case where a property exists on both, there are a few cases:

    1. Name: In this case, we keep the shorter name as the "name" and set the
       longer name as an "other_name". We also move all "other names" from
       source to dest. The reasoning here is that the shorter name is more
       likely to be the common name a candidate is known by.

    2. Images: The source person's primary image is moved to the dest person's
       primary image, all other images are moved from source to dest

    3. Person Identifiers: identifiers missing from dest will be added from
       source. Where an ID of a given value type exists on both, the newer
       Person Identifier is used, based on it's modified datetime.
    """

    # Map between field names and the method that merges them
    SUPPORTED_FIELDS = OrderedDict(
        (
            # Person attrs
            ("honorific_prefix", "merge_person_attrs"),
            ("name", "merge_name_and_other_names"),
            ("honorific_suffix", "merge_person_attrs"),
            ("gender", "merge_person_attrs"),
            ("birth_date", "merge_person_attrs"),
            ("death_date", "merge_person_attrs"),
            ("biography", "merge_person_attrs"),
            ("other_names", "merge_name_and_other_names"),
            ("family_name", "merge_person_attrs"),
            ("national_identity", "merge_person_attrs"),
            ("sort_name", "merge_person_attrs"),
            ("additional_name", "merge_person_attrs"),
            ("favourite_biscuit", "merge_person_attrs"),
            ("given_name", "merge_person_attrs"),
            ("patronymic_name", "merge_person_attrs"),
            ("summary", "merge_person_attrs"),
            ("delisted", "merge_person_attrs"),
            ("name_search_vector", "discard_data"),
            # Relations
            ("versions", "merge_versions_json"),
            ("tmp_person_identifiers", "merge_person_identifiers"),
            ("image", "merge_images"),
            ("loggedaction", "merge_logged_actions"),
            ("memberships", "merge_memberships"),
            ("queuedimage", "merge_queued_images"),
            ("not_standing", "merge_not_standing"),
            ("resultevent", "merge_result_events"),
            ("gender_guess", "merge_gender_guess"),
            ("facebookadvert", "merge_facebookadvert"),
            ("duplicate_suggestion", "merge_duplicate_suggestion"),
            ("duplicate_suggestion_other_person", "merge_duplicate_suggestion"),
            # Discarded
            ("id", "discard_data"),
            ("created", "discard_data"),
            ("modified", "discard_data"),
            ("edit_limitations", "discard_data"),
            ("sources", "discard_data"),
        )
    )

    def __init__(self, person_a, person_b, request=None):
        """
        The params are called person A and B because we don't yet know
        what we'll use as source and dest.

        Request it optional, and used for creating logged actions
        :type person_a: people.models.Person
        :type person_b: people.models.Person
        :param request:
        """

        self.dest_person, self.source_person = sorted(
            [person_a, person_b], key=lambda m: m.pk
        )
        assert self.dest_person.pk < self.source_person.pk

        self.request = request

    def safe_delete(self, model, with_logged_action=False):
        collector = NestedObjects(using=connection.cursor().db.alias)
        collector.collect([model])
        if len(collector.nested()) > 1:
            related_objects = "\n\t".join(
                [repr(m) for m in collector.nested()[1:]]
            )
            raise UnsafeToDelete(
                "Can't delete '{}' with related objects: \n {}".format(
                    model, related_objects
                )
            )

        if with_logged_action:
            return model.delete_with_logged_action(
                user=self.request.user,
                source=f"Person merged with {self.dest_person.pk}",
            )
        return model.delete()

    def _invalidate_pi_cache(self):
        for person in [self.source_person, self.dest_person]:
            person.invalidate_identifier_cache()

    def discard_data(self):
        """
        A no-op method that will discard data when merging.

        Used by self. SUPPORTED_FIELDS to explicetly mark some fields
        as discarded.
        """
        pass

    def merge_versions_json(self):
        # Merge the reduced JSON representations:
        merge_popit_people(
            get_person_as_version_data(self.dest_person),
            get_person_as_version_data(self.source_person),
        )

        # Make sure the secondary person's version history is appended, so it
        # isn't lost.
        dest_person_versions = self.dest_person.versions
        dest_person_versions += self.source_person.versions
        self.dest_person.versions = dest_person_versions

    @property
    def person_attrs_to_merge(self):
        """
        Build a list of person attrs to be merged. Name is excluded from this
        list as it is handled by the merge_name_and_other_names method
        """
        attrs_to_merge = [f.name for f in settings.SIMPLE_POPOLO_FIELDS]
        attrs_to_merge += [
            "favourite_biscuit",
            "additional_name",
            "sort_name",
            "national_identity",
            "family_name",
            "given_name",
            "patronymic_name",
            "summary",
        ]
        # name is handled seperately because it does not
        attrs_to_merge.remove("name")
        return attrs_to_merge

    def merge_person_attrs(self):
        """
        Merge attributes on Person from source in to dest.

        Because source is a higher ID, and therefore newer, we assume that it's
        attributes should be kept, replacing dest's.
        """
        for field_name in self.person_attrs_to_merge:
            source_value = getattr(self.source_person, field_name, None)

            # Assume we want to keep the value from source
            if source_value:
                setattr(self.dest_person, field_name, source_value)

    def merge_name_and_other_names(self):
        """
        If names are different, set the shorter name as the main 'name' as this
        is more likely to be their common name, and store the longer name as an
        'other_name'. Also make sure we store any more 'other_name' values from
        the source person.
        """
        dest_name = self.dest_person.name
        source_name = self.source_person.name

        if dest_name != source_name:
            shorter_name, longer_name = sorted(
                [source_name, dest_name], key=len
            )
            self.dest_person.name = shorter_name
            self.dest_person.other_names.update_or_create(name=longer_name)

        for other_name in self.source_person.other_names.all():
            self.dest_person.other_names.update_or_create(name=other_name.name)
            other_name.delete()

    def merge_images(self):
        # Change the secondary person's image to point at the primary
        # person's image instead:
        try:
            new_image = self.source_person.image
        except PersonImage.DoesNotExist:
            return
        # There's an existing image on source, so replace the dest
        # person's image (assume the source image is better)
        with contextlib.suppress(PersonImage.DoesNotExist):
            self.dest_person.image.delete()

        new_image.person = self.dest_person
        new_image.save()

    def _resolve_duplicate_identifiers(self, i1, i2):
        # Get the newer ID of the two
        keep, delete = sorted([i1, i2], key=lambda m: m.modified, reverse=True)
        self.safe_delete(delete)
        keep.person = self.dest_person
        keep.save()

    def merge_person_identifiers(self):
        """
        Because we store the modified datetime for PersonIdentifiers,
        we can just keep the latest version from either source or dest.
        """

        duplicate_pi_values = self.source_person.tmp_person_identifiers.filter(
            value__in=self.dest_person.tmp_person_identifiers.all().values_list(
                "value", flat=True
            )
        )
        for pi in duplicate_pi_values:
            self._resolve_duplicate_identifiers(
                pi, self.dest_person.tmp_person_identifiers.get(value=pi.value)
            )
        if duplicate_pi_values:
            self._invalidate_pi_cache()

        qs = self.source_person.tmp_person_identifiers.all()
        moved_any = qs.exists()
        for identifier in qs:
            existing_of_type = self.dest_person.get_single_identifier_of_type(
                identifier.value_type
            )
            if existing_of_type:
                self._resolve_duplicate_identifiers(
                    existing_of_type, identifier
                )
            else:
                identifier.person = self.dest_person
                identifier.save()

        if moved_any:
            self._invalidate_pi_cache()

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
                raise InvalidMergeError(
                    "Trying to merge two Memberships with results"
                )
            msource.result.membership = mdest
            mdest.result.save()
            # if we have a result we also update if they were elected
            mdest.elected = msource.elected
            mdest.save()

        # copy any previous party allifiations if this is for a welsh run ballot
        if msource.ballot.is_welsh_run:
            for previous_party in msource.previous_party_affiliations.all():
                mdest.previous_party_affiliations.add(previous_party)
                msource.previous_party_affiliations.remove(previous_party)

        self.safe_delete(msource)

    def merge_memberships(self):
        for membership in self.source_person.memberships.all():
            existing_membership_qs = self.dest_person.memberships.filter(
                ballot=membership.ballot
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
        # Check that we've not caused duplicate (membership, election) pairs.
        # We need to do this manually because we can't add a DB constraint
        # spanning the three tables (Membership->Ballot->Election)
        person_elections = {
            mem.ballot.election_id
            for mem in self.dest_person.memberships.select_related("ballot")
        }
        if len(person_elections) != self.dest_person.memberships.count():
            raise InvalidMergeError(
                "Merging would cause this person to be standing more than once in the same election"
            )

    def merge_queued_images(self):
        self.source_person.queuedimage_set.update(person=self.dest_person)

    def merge_facebookadvert(self):
        self.source_person.facebookadvert_set.update(person=self.dest_person)

    def merge_not_standing(self):
        for election in self.source_person.not_standing.all():
            if not self.dest_person.memberships.filter(
                ballot__election=election
            ):
                # If this election is in the dest person's memberships, we
                # shouldn't add to their "not standing" list.
                self.dest_person.not_standing.add(election)
            self.source_person.not_standing.remove(election)

    def merge_result_events(self):
        ResultEvent.objects.filter(winner=self.source_person).update(
            winner=self.dest_person
        )

    def merge_gender_guess(self):
        """
        Just delete the source guess – this is data we generate from the
        name so it's not important
        """
        if hasattr(self.source_person, "gender_guess"):
            self.source_person.gender_guess.delete()

    def merge_duplicate_suggestion(self):
        alter_duplicate_suggestion_post_merge(
            self.source_person, self.dest_person
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
        left, and is deleted safely using `self.safe_delete`
        """
        with transaction.atomic():
            # Merge all the things
            for method_name in set(self.SUPPORTED_FIELDS.values()):
                method = getattr(self, method_name)
                method()

            # Post merging tasks
            # Save the dest person (don't assume the methods above do this)
            change_metadata = get_change_metadata(
                self.request,
                "After merging person {}".format(self.source_person.pk),
            )
            # Save the dest person before creating a LoggedAction
            # See https://github.com/DemocracyClub/yournextrepresentative/issues/1037
            # for more
            self.dest_person.record_version(change_metadata)
            self.dest_person.save()

            # Log that the merge has taken place, and will be shown in
            # the recent changes, leaderboards, etc.
            if self.request:
                LoggedAction.objects.create(
                    user=self.request.user,
                    action_type=ActionType.PERSON_MERGE,
                    ip_address=get_client_ip(self.request),
                    popit_person_new_version=change_metadata["version_id"],
                    person=self.dest_person,
                    source=change_metadata["information_source"],
                )

            self.setup_redirect()

            if delete:
                self.safe_delete(
                    self.source_person, with_logged_action=bool(self.request)
                )
        return self.dest_person
