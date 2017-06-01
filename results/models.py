from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models

from popolo.models import Organization, Person, Post
from elections.models import Election
from candidates.models import OrganizationExtra

class ResultEvent(models.Model):

    class Meta:
        ordering = ['created']

    created = models.DateTimeField(auto_now_add=True)
    election = models.ForeignKey(Election, blank=True, null=True)
    winner = models.ForeignKey(Person)
    old_post_id = models.CharField(blank=False, max_length=256)
    old_post_name = models.CharField(blank=True, null=True, max_length=1024)
    post = models.ForeignKey(Post, blank=True, null=True)
    winner_party = models.ForeignKey(Organization, blank=True, null=True)
    source = models.CharField(max_length=512)
    user = models.ForeignKey(User, blank=True, null=True)
    proxy_image_url_template = \
        models.CharField(blank=True, null=True, max_length=1024)
    parlparse_id = models.CharField(blank=True, null=True, max_length=256)

    @property
    def winner_party_name(self):
        return OrganizationExtra.objects \
            .select_related('base') \
            .get(
                slug=self.winner_party_id
            ).base.name
