from django.contrib.auth.models import User
from django.db import models

from elections.models import Election
from popolo.models import Post


class ResultEvent(models.Model):
    class Meta:
        ordering = ["created"]

    created = models.DateTimeField(auto_now_add=True)
    election = models.ForeignKey(
        Election, blank=True, null=True, on_delete=models.CASCADE
    )
    winner = models.ForeignKey("people.Person", on_delete=models.CASCADE)
    old_post_id = models.CharField(blank=False, max_length=256)
    old_post_name = models.CharField(blank=True, null=True, max_length=1024)
    post = models.ForeignKey(
        Post, blank=True, null=True, on_delete=models.CASCADE
    )
    winner_party = models.ForeignKey("parties.Party", on_delete=models.CASCADE)
    source = models.CharField(max_length=512)
    user = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.CASCADE
    )
    parlparse_id = models.CharField(blank=True, null=True, max_length=256)
    retraction = models.BooleanField(default=False)

    @property
    def short_post_name(self):
        if self.post:
            return self.post.short_label
        return self.old_post_name

    @property
    def image_url_path(self):
        url_path = ""
        for image in self.winner.images.all():
            if image.is_primary:
                url_path = image.image.url
                break
        return url_path
