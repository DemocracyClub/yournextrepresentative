from django.db import models


class ExtraField(models.Model):
    class Meta:
        ordering = ("order",)

    LINE = "line"
    LONGER_TEXT = "longer-text"
    URL = "url"
    YESNO = "yesno"

    FIELD_TYPES = (
        (LINE, "A single line of text"),
        (LONGER_TEXT, "One or more paragraphs of text"),
        (URL, "A URL"),
        (YESNO, "A Yes/No/Don't know dropdown"),
    )

    key = models.CharField(max_length=256)
    type = models.CharField(max_length=64, choices=FIELD_TYPES)
    label = models.CharField(max_length=1024)
    order = models.IntegerField(blank=True, default=0)

    def __str__(self):
        return self.key


class PersonExtraFieldValue(models.Model):
    class Meta:
        unique_together = ("person", "field")

    person = models.ForeignKey(
        "people.Person", related_name="extra_field_values"
    )
    field = models.ForeignKey(ExtraField)
    value = models.TextField(blank=True)
