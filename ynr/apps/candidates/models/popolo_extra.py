from datetime import date
from os.path import join
import re

from django.conf import settings
from django.contrib.admin.utils import NestedObjects
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from django.core.files.storage import DefaultStorage
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext as _

from dateutil import parser
from slugify import slugify

from elections.models import Election, AreaType
from images.models import Image, HasImageMixin

"""Extensions to the base django-popolo classes for YourNextRepresentative

These are done via explicit one-to-one fields to avoid the performance
problems with multi-table inheritance; it's preferable to state when you
want a join or not.

  http://stackoverflow.com/q/23466577/223092

"""


class UnsafeToDelete(Exception):
    pass


def raise_if_unsafe_to_delete(base_object):
    if not paired_object_safe_to_delete(base_object):
        msg = "Trying to delete a {model} (pk={pk}) that other " "objects that depend on"
        raise UnsafeToDelete(
            msg.format(
                model=base_object._meta.model.__name__, pk=base_object.id
            )
        )


def paired_object_safe_to_delete(base_object):
    collector = NestedObjects(using="default")
    collector.collect([base_object])
    collected = collector.nested()
    if len(collected) > 2:
        return False
    assert collected[0] == base_object
    if len(collected) == 1:
        return True
    if len(collected[1]) != 1:
        return False
    return True


class OrganizationExtra(HasImageMixin, models.Model):
    base = models.OneToOneField("popolo.Organization", related_name="extra")
    slug = models.CharField(max_length=256, blank=True, unique=True)

    # For parties, which party register is it on:
    register = models.CharField(blank=True, max_length=512)

    images = GenericRelation(Image)

    def __str__(self):
        # WARNING: This will cause an extra query when getting the
        # repr() or unicode() of this object unless the base object
        # has been select_related.
        return self.base.name

    def ec_id(self):
        try:
            party_id = self.base.identifiers.filter(
                scheme="electoral-commission"
            ).first()
            return party_id.identifier
        except:
            return "ynmp-party:2"


class PostExtra(HasImageMixin, models.Model):
    base = models.OneToOneField("popolo.Post", related_name="extra")
    slug = models.CharField(max_length=256, blank=True, unique=True)

    elections = models.ManyToManyField(
        Election, related_name="posts", through="PostExtraElection"
    )
    group = models.CharField(max_length=1024, blank=True)
    party_set = models.ForeignKey("PartySet", blank=True, null=True)

    def __str__(self):
        # WARNING: This will cause an extra query when getting the
        # repr() or unicode() of this object unless the base object
        # has been select_related.
        return self.base.label

    @property
    def short_label(self):
        from candidates.election_specific import shorten_post_label

        return shorten_post_label(self.base.label)


class PostExtraElection(models.Model):
    postextra = models.ForeignKey(PostExtra)
    election = models.ForeignKey(Election)
    ballot_paper_id = models.CharField(blank=True, max_length=255, unique=True)

    candidates_locked = models.BooleanField(default=False)
    winner_count = models.IntegerField(blank=True, null=True)

    class Meta:
        unique_together = ("election", "postextra")

    def __repr__(self):
        fmt = "<PostExtraElection ballot_paper_id='{e}'{l}{w}>"
        return fmt.format(
            e=self.ballot_paper_id,
            l=(" candidates_locked=True" if self.candidates_locked else ""),
            w=(
                " winner_count={}".format(self.winner_count)
                if (self.winner_count is not None)
                else ""
            ),
        )

    def get_absolute_url(self):
        return reverse(
            "constituency",
            args=[
                self.election.slug,
                self.postextra.slug,
                slugify(self.postextra.short_label),
            ],
        )


class AreaExtra(models.Model):
    base = models.OneToOneField("popolo.Area", related_name="extra")

    type = models.ForeignKey(
        AreaType, blank=True, null=True, related_name="areas"
    )

    def __str__(self):
        # WARNING: This will cause an extra query when getting the
        # repr() or unicode() of this object unless the base object
        # has been select_related.
        return self.base.name


class PartySet(models.Model):
    slug = models.CharField(max_length=256, unique=True)
    name = models.CharField(max_length=1024)
    parties = models.ManyToManyField(
        "popolo.Organization", related_name="party_sets"
    )

    def __str__(self):
        return self.name

    def party_choices_basic(self):
        result = list(self.parties.order_by("name").values_list("id", "name"))
        result.insert(0, ("", ""))
        return result

    def party_choices(
        self,
        include_descriptions=True,
        exclude_deregistered=False,
        include_description_ids=False,
        include_non_current=True,
    ):
        # For various reasons, we've found it's best to order the
        # parties by those that have the most candidates - this means
        # that the commonest parties to select are at the top of the
        # drop down.  The logic here tries to build such an ordered
        # list of candidates if there are enough that such an ordering
        # makes sense.  Otherwise the fallback is to rank
        # alphabetically.
        from popolo.models import Membership

        candidacies_ever_qs = (
            self.parties.all()
            .annotate(
                membership_count=models.Count("memberships_on_behalf_of__pk")
            )
            .order_by("-membership_count", "name")
            .only("end_date", "name")
        )

        parties_current_qs = (
            self.parties.filter(
                memberships_on_behalf_of__post_election__election__current=True
            )
            .annotate(
                membership_count=models.Count("memberships_on_behalf_of__pk")
            )
            .order_by("-membership_count", "name")
            .only("end_date", "name")
        )

        if not include_non_current:
            parties_current_qs = parties_current_qs.exclude(membership_count=0)

        parties_notcurrent_qs = (
            self.parties.filter(
                ~models.Q(
                    memberships_on_behalf_of__post_election__election__current=True
                )
            )
            .annotate(membership_count=models.Value(0, models.IntegerField()))
            .order_by("-membership_count", "name")
            .only("end_date", "name")
        )

        minimum_count = settings.CANDIDATES_REQUIRED_FOR_WEIGHTED_PARTY_LIST

        total_memberships = Membership.objects.all()
        current_memberships = total_memberships.filter(
            post_election__election__current=True
        )

        queries = []
        if current_memberships.count() > minimum_count:
            queries.append(parties_current_qs)
            if include_non_current:
                queries.append(parties_notcurrent_qs)
        elif total_memberships.count() > minimum_count:
            queries.append(candidacies_ever_qs)
        else:
            return self.party_choices_basic()

        result = [("", "")]
        parties_with_candidates = []

        for qs in queries:
            if include_descriptions:
                qs = qs.prefetch_related("other_names")
            for party in qs:
                parties_with_candidates.append(party)
                count_string = ""
                if party.membership_count:
                    count_string = " ({} candidates)".format(
                        party.membership_count
                    )

                name = _("{party_name}{count_string}").format(
                    party_name=party.name, count_string=count_string
                )

                if party.end_date:
                    party_end_date = parser.parse(party.end_date).date()
                    if date.today() > party_end_date:
                        if exclude_deregistered:
                            continue
                        name = "{} (Deregistered {})".format(
                            name, party.end_date
                        )

                if include_descriptions and party.other_names.exists():
                    names = [(party.pk, party.name)]
                    for other_name in party.other_names.all():
                        joint_text = re.compile(r"joint descriptions? with")
                        party_id_str = str(party.pk)
                        if include_description_ids:
                            party_id_str = "{}__{}".format(
                                party_id_str, other_name.pk
                            )
                        if not joint_text.search(other_name.name.lower()):
                            names.append((party_id_str, other_name.name))
                    party_names = (name, (names))
                else:
                    party_names = (str(party.pk), name)

                result.append(party_names)
        return result


class ImageExtraManager(models.Manager):
    def create_from_file(
        self, image_filename, ideal_relative_name, base_kwargs, extra_kwargs
    ):
        # Import the file to media root and create the ORM
        # objects.
        storage = DefaultStorage()
        desired_storage_path = join("images", ideal_relative_name)
        with open(image_filename, "rb") as f:
            storage_filename = storage.save(desired_storage_path, f)
        image = Image.objects.create(image=storage_filename, **base_kwargs)
        return ImageExtra.objects.create(base=image, **extra_kwargs)

    def update_or_create_from_file(
        self, image_filename, ideal_relative_name, defaults, **kwargs
    ):
        try:
            image_extra = ImageExtra.objects.select_related("base").get(
                **kwargs
            )
            for k, v in defaults.items():
                if k.startswith("base__"):
                    base_k = re.sub(r"^base__", "", k)
                    setattr(image_extra.base, base_k, v)
                else:
                    setattr(image_extra, k, v)
            image_extra.save()
            image_extra.base.save()
            return image_extra, False
        except ImageExtra.DoesNotExist:
            # Prepare args for the base object first:
            base_kwargs = {
                re.sub(r"base__", "", k): v
                for k, v in defaults.items()
                if k.startswith("base__")
            }
            base_kwargs.update(
                {
                    re.sub(r"base__", "", k): v
                    for k, v in kwargs.items()
                    if k.startswith("base__")
                }
            )
            # And now the extra object:
            extra_kwargs = {
                k: v for k, v in defaults.items() if not k.startswith("base__")
            }
            extra_kwargs.update(
                {k: v for k, v in kwargs.items() if not k.startswith("base__")}
            )
            image_extra = self.create_from_file(
                image_filename, ideal_relative_name, base_kwargs, extra_kwargs
            )
        return image_extra


class ImageExtra(models.Model):
    base = models.OneToOneField(Image, related_name="extra")

    copyright = models.CharField(max_length=64, default="other", blank=True)
    uploading_user = models.ForeignKey(User, blank=True, null=True)
    user_notes = models.TextField(blank=True)
    md5sum = models.CharField(max_length=32, blank=True)
    user_copyright = models.CharField(max_length=128, blank=True)
    notes = models.TextField(blank=True)

    objects = ImageExtraManager()
