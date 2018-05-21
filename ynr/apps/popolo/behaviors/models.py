try:
    from django.contrib.contenttypes.fields import GenericForeignKey
except ImportError:
    # This fallback import is the version that was deprecated in
    # Django 1.7 and is removed in 1.9:
    from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.fields import AutoCreatedField, AutoLastModifiedField
from datetime import datetime

__author__ = 'guglielmo'


class GenericRelatable(models.Model):
    """
    An abstract class that provides the possibility of generic relations
    """
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True


def validate_partial_date(value):
    """
    Validate a partial date, it can be partial, but it must yet be a valid date.
    Accepted formats are: YYYY-MM-DD, YYYY-MM, YYYY.
    2013-22 must rais a ValidationError, as 2013-13-12, or 2013-11-55.
    """
    try:
        datetime.strptime(value, '%Y-%m-%d')
    except ValueError:
        try:
            datetime.strptime(value, '%Y-%m')
        except ValueError:
            try:
                datetime.strptime(value, '%Y')
            except ValueError:
                raise ValidationError(u'date seems not to be correct %s' % value)


class Dateframeable(models.Model):
    """
    An abstract base class model that provides a start and an end dates to the class.
    Uncomplete dates can be used. The validation pattern is: "^[0-9]{4}(-[0-9]{2}){0,2}$"
    """
    partial_date_validator = RegexValidator(regex="^[0-9]{4}(-[0-9]{2}){0,2}$", message="Date has wrong format")

    start_date = models.CharField(
        _("start date"), max_length=10, blank=True, null=True,
        validators=[partial_date_validator, validate_partial_date],
        help_text=_("The date when the validity of the item starts"),
    )
    end_date = models.CharField(
        _("end date"), max_length=10, blank=True, null=True,
        validators=[partial_date_validator, validate_partial_date],
        help_text=_("The date when the validity of the item ends")
    )

    class Meta:
        abstract = True


class Timestampable(models.Model):
    """
    An abstract base class model that provides self-updating
    ``created`` and ``modified`` fields.
    """
    created_at = AutoCreatedField(_('creation time'))
    updated_at = AutoLastModifiedField(_('last modification time'))

    class Meta:
        abstract = True
