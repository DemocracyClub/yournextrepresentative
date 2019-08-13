from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import connection
from django.urls import reverse

from .managers import WombleQuerySet


class WombleTags(models.Model):
    label = models.CharField(max_length=255)

    class Meta:
        ordering = ("label",)

    @property
    def label_html(self):
        return self.label.title()

    @property
    def label_emoji(self):
        text = self.label
        if text == "superwomble":
            text = "🎉 {} 🎉".format(text)

        if text == "Results Raccoon":
            text = "🦝 {} 🦝".format(text)

        if text == "inactive":
            text = "😢 {} 😢".format(text)

        if text == "Photo Uploader":
            text = "📷 {} 📷".format(text)

        if text == "Photo Editor":
            text = "🖼️ {} 🖼️".format(text)

        return text.title()

    def get_absolute_url(self):
        return reverse("womble_tag", args=[self.label])


class WombleProfile(models.Model):
    user = models.OneToOneField("auth.User", related_name="womble_profile")
    tags = models.ManyToManyField(WombleTags)

    objects = WombleQuerySet.as_manager()

    def __str__(self):
        return str(self.user.pk)

    def get_absolute_url(self):
        return reverse("single_womble", args=[self.user.pk])

    def edits_over_time(self):
        cursor = connection.cursor()

        cursor.execute(
            """
              WITH range_values AS (
              SELECT date_trunc('week', min(created)) as minval,
                     date_trunc('week', max(created)) as maxval
              FROM candidates_loggedaction WHERE user_id=%s),

            week_range AS (
              SELECT generate_series(minval, maxval, '1 week'::interval) as week
              FROM range_values
            ),

            weekly_counts AS (
              SELECT date_trunc('week', created) as week,
                     count(*) as ct
              FROM candidates_loggedaction
              WHERE user_id=%s
              GROUP BY 1
            )

            SELECT week_range.week,
                   weekly_counts.ct
            FROM week_range
            LEFT OUTER JOIN weekly_counts on week_range.week = weekly_counts.week;
        """,
            (self.user.pk, self.user.pk),
        )

        return cursor.fetchall()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        WombleProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.womble_profile.save()
