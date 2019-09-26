from collections import OrderedDict
from datetime import date

from django.contrib.admin.utils import NestedObjects
from django.db import connection, models
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone


class ElectionQuerySet(models.QuerySet):
    def current(self, current=True):
        return self.filter(current=current)

    def future(self):
        return self.filter(election_date__gt=timezone.now())

    def current_or_future(self):
        return self.filter(
            models.Q(current=True) | models.Q(election_date__gt=timezone.now())
        )

    def get_by_slug(self, election):
        return get_object_or_404(self, slug=election)

    def by_date(self):
        return self.order_by("election_date")


class ElectionManager(models.Manager):
    def are_upcoming_elections(self):
        today = date.today()
        return self.current().filter(election_date__gte=today).exists()


class Election(models.Model):
    slug = models.CharField(max_length=128, unique=True)
    for_post_role = models.CharField(max_length=128)
    winner_membership_role = models.CharField(
        max_length=128, null=True, blank=True
    )
    candidate_membership_role = models.CharField(max_length=128)
    election_date = models.DateField(db_index=True)
    name = models.CharField(max_length=128)
    current = models.BooleanField()
    use_for_candidate_suggestions = models.BooleanField(default=False)
    organization = models.ForeignKey(
        "popolo.Organization", null=True, blank=True, on_delete=models.CASCADE
    )
    party_lists_in_use = models.BooleanField(default=False)
    people_elected_per_post = models.IntegerField(
        default=1,
        help_text=(
            "The number of people who are elected to this post in the "
            "election.  -1 means a variable number of winners"
        ),
    )
    default_party_list_members_to_show = models.IntegerField(default=0)
    show_official_documents = models.BooleanField(default=False)
    ocd_division = models.CharField(max_length=250, blank=True)

    description = models.CharField(max_length=500, blank=True)

    objects = ElectionManager.from_queryset(ElectionQuerySet)()
    UnsafeToDelete = Exception

    def __str__(self):
        return self.name

    def get_absolute_url(self, request=None):
        return reverse("election_view", kwargs={"election": self.slug})

    @property
    def in_past(self):
        return self.election_date < date.today()

    @classmethod
    def group_and_order_elections(cls, include_ballots=False, for_json=False):
        """Group elections in a helpful order

        We should order and group elections in the following way:

          Group by current_or_future=True, then current=False
            Group election by election date (new to old)
              Group by for_post_role (ordered alphabetically)
                Order by election name

        If the parameter include_ballots is set to True, then
        the ballots will be included as well. If for_json is
        True, the returned data should be safe to serialize to JSON (e.g.
        the election dates will be ISO 8601 date strings (i.e. YYYY-MM-DD)
        rather than datetime.date objects).

        e.g. An example of the returned data structure:

        [
          {
            'current_or_future': True,
            'dates': OrderedDict([(datetime.date(2015, 5, 7), [
              {
                'role': 'Member of Parliament',
                'elections': [
                  {
                    'election': <Election: 2015 General Election>,
                    'ballots': [
                      <Post: Member of Parliament for Aberavon>,
                      <Post: Member of Parliament for Aberconwy>,
                      ...
                    ]
                  }
                ]
              }
            ]),
            (datetime.date(2016, 5, 5), [
              {
                'role': 'Member of the Scottish Parliament',
                'elections': [
                  {
                    'election': <Election: 2016 Scottish Parliament Election (Regions)>,
                     'ballots': [
                       <Post: Member of the Scottish Parliament for Central Scotland>,
                       <Post: Member of the Scottish Parliament for Glasgow>,
                       ...
                     ]
                  },
                  {
                    'election': <Election: 2016 Scottish Parliament Election (Constituencies)>,
                    'ballots': [
                      <Post: Member of the Scottish Parliament for Aberdeen Central>,
                      <Post: Member of the Scottish Parliament for Aberdeen Donside>,
                      ...
                    ]
                  }
                ]
              }
            ])])
          },
          {
            'current_or_future': False,
            'dates': OrderedDict([(datetime.date(2010, 5, 6), [
              {
                'role': 'Member of Parliament',
                'elections': [
                  {
                    'election': <Election: 2010 General Election>,
                    'ballots': [
                      <Post: Member of Parliament for Aberavon>,
                      <Post: Member of Parliament for Aberconwy>,
                      ...
                    ]
                  }
                ]
              }
            ])])
          }
        ]

        """
        from candidates.models import Ballot

        result = [{"current_or_future": True, "dates": OrderedDict()}]
        result.append({"current_or_future": False, "dates": OrderedDict()})

        role = None
        qs = cls.objects.order_by(
            "election_date", "-current", "for_post_role", "name"
        )
        # If we've been asked to include ballots as well, add a prefetch
        # to the queryset:
        if include_ballots:
            qs = qs.prefetch_related(
                models.Prefetch(
                    "ballot_set",
                    Ballot.objects.select_related("post")
                    .order_by("post__label")
                    .prefetch_related("suggestedpostlock_set"),
                )
            )

        # The elections and ballots are already sorted into the right
        # order, but now need to be grouped into the useful
        # data structure described in the docstring.
        last_current = None
        for election in qs:
            current_or_future = election.current or not election.in_past
            current_index = 1 - int(current_or_future)
            if for_json:
                election_date = election.election_date.isoformat()
            else:
                election_date = election.election_date
            roles = result[current_index]["dates"].setdefault(election_date, [])
            # If the role has changed, or the election date has changed,
            # or we've switched from current elections to past elections,
            # create a new array of elections to append to:
            if (
                (role is None)
                or role["role"] != election.for_post_role
                or role["elections"][0]["election"].election_date
                != election_date
                or (
                    last_current is not None
                    and last_current != current_or_future
                )
            ):
                role = {"role": election.for_post_role, "elections": []}
                roles.append(role)
            d = {"election": election}
            if include_ballots:
                d["ballots"] = list(election.ballot_set.all())
            role["elections"].append(d)
            last_current = current_or_future

        return result

    def safe_delete(self):
        if self.current:
            raise self.UnsafeToDelete(
                "Can't delete 'current' election {}".format(self.slug)
            )

        collector = NestedObjects(using=connection.cursor().db.alias)
        collector.collect([self])
        if len(collector.nested()) > 1:
            raise self.UnsafeToDelete(
                "Can't delete election {} with related objects".format(
                    self.slug
                )
            )

        self.delete()
