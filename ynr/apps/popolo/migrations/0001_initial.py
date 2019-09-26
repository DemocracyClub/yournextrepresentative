import django.core.validators
import django.utils.timezone
import model_utils.fields
from django.db import migrations, models

import popolo.behaviors.models


class Migration(migrations.Migration):

    dependencies = [("contenttypes", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="ContactDetail",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("object_id", models.PositiveIntegerField()),
                (
                    "start_date",
                    models.CharField(
                        validators=[
                            django.core.validators.RegexValidator(
                                regex=b"^[0-9]{4}(-[0-9]{2}){0,2}$",
                                message=b"Date has wrong format",
                            ),
                            popolo.behaviors.models.validate_partial_date,
                        ],
                        max_length=10,
                        blank=True,
                        help_text="The date when the validity of the item starts",
                        null=True,
                        verbose_name="start date",
                    ),
                ),
                (
                    "end_date",
                    models.CharField(
                        validators=[
                            django.core.validators.RegexValidator(
                                regex=b"^[0-9]{4}(-[0-9]{2}){0,2}$",
                                message=b"Date has wrong format",
                            ),
                            popolo.behaviors.models.validate_partial_date,
                        ],
                        max_length=10,
                        blank=True,
                        help_text="The date when the validity of the item ends",
                        null=True,
                        verbose_name="end date",
                    ),
                ),
                (
                    "created_at",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        verbose_name="creation time",
                        editable=False,
                    ),
                ),
                (
                    "updated_at",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        verbose_name="last modification time",
                        editable=False,
                    ),
                ),
                (
                    "label",
                    models.CharField(
                        help_text="A human-readable label for the contact detail",
                        max_length=128,
                        verbose_name="label",
                        blank=True,
                    ),
                ),
                (
                    "contact_type",
                    models.CharField(
                        help_text="A type of medium, e.g. 'fax' or 'email'",
                        max_length=12,
                        verbose_name="type",
                        choices=[
                            (b"FAX", "Fax"),
                            (b"PHONE", "Telephone"),
                            (b"MOBILE", "Mobile"),
                            (b"EMAIL", "Email"),
                            (b"MAIL", "Snail mail"),
                            (b"TWITTER", "Twitter"),
                            (b"FACEBOOK", "Facebook"),
                        ],
                    ),
                ),
                (
                    "value",
                    models.CharField(
                        help_text="A value, e.g. a phone number or email address",
                        max_length=128,
                        verbose_name="value",
                    ),
                ),
                (
                    "note",
                    models.CharField(
                        help_text="A note, e.g. for grouping contact details by physical location",
                        max_length=128,
                        verbose_name="note",
                        blank=True,
                    ),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        to="contenttypes.ContentType", on_delete=models.CASCADE
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Identifier",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("object_id", models.PositiveIntegerField()),
                (
                    "identifier",
                    models.CharField(
                        help_text="An issued identifier, e.g. a DUNS number",
                        max_length=128,
                        verbose_name="identifier",
                    ),
                ),
                (
                    "scheme",
                    models.CharField(
                        help_text="An identifier scheme, e.g. DUNS",
                        max_length=128,
                        verbose_name="scheme",
                        blank=True,
                    ),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        to="contenttypes.ContentType", on_delete=models.CASCADE
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Link",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("object_id", models.PositiveIntegerField()),
                ("url", models.URLField(help_text="A URL", verbose_name="url")),
                (
                    "note",
                    models.CharField(
                        help_text="A note, e.g. 'Wikipedia page'",
                        max_length=128,
                        verbose_name="note",
                        blank=True,
                    ),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        to="contenttypes.ContentType", on_delete=models.CASCADE
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Membership",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "start_date",
                    models.CharField(
                        validators=[
                            django.core.validators.RegexValidator(
                                regex=b"^[0-9]{4}(-[0-9]{2}){0,2}$",
                                message=b"Date has wrong format",
                            ),
                            popolo.behaviors.models.validate_partial_date,
                        ],
                        max_length=10,
                        blank=True,
                        help_text="The date when the validity of the item starts",
                        null=True,
                        verbose_name="start date",
                    ),
                ),
                (
                    "end_date",
                    models.CharField(
                        validators=[
                            django.core.validators.RegexValidator(
                                regex=b"^[0-9]{4}(-[0-9]{2}){0,2}$",
                                message=b"Date has wrong format",
                            ),
                            popolo.behaviors.models.validate_partial_date,
                        ],
                        max_length=10,
                        blank=True,
                        help_text="The date when the validity of the item ends",
                        null=True,
                        verbose_name="end date",
                    ),
                ),
                (
                    "created_at",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        verbose_name="creation time",
                        editable=False,
                    ),
                ),
                (
                    "updated_at",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        verbose_name="last modification time",
                        editable=False,
                    ),
                ),
                (
                    "label",
                    models.CharField(
                        help_text="A label describing the membership",
                        max_length=128,
                        verbose_name="label",
                        blank=True,
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        help_text="The role that the person fulfills in the organization",
                        max_length=128,
                        verbose_name="role",
                        blank=True,
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Organization",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "start_date",
                    models.CharField(
                        validators=[
                            django.core.validators.RegexValidator(
                                regex=b"^[0-9]{4}(-[0-9]{2}){0,2}$",
                                message=b"Date has wrong format",
                            ),
                            popolo.behaviors.models.validate_partial_date,
                        ],
                        max_length=10,
                        blank=True,
                        help_text="The date when the validity of the item starts",
                        null=True,
                        verbose_name="start date",
                    ),
                ),
                (
                    "end_date",
                    models.CharField(
                        validators=[
                            django.core.validators.RegexValidator(
                                regex=b"^[0-9]{4}(-[0-9]{2}){0,2}$",
                                message=b"Date has wrong format",
                            ),
                            popolo.behaviors.models.validate_partial_date,
                        ],
                        max_length=10,
                        blank=True,
                        help_text="The date when the validity of the item ends",
                        null=True,
                        verbose_name="end date",
                    ),
                ),
                (
                    "created_at",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        verbose_name="creation time",
                        editable=False,
                    ),
                ),
                (
                    "updated_at",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        verbose_name="last modification time",
                        editable=False,
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="A primary name, e.g. a legally recognized name",
                        max_length=128,
                        verbose_name="name",
                    ),
                ),
                (
                    "classification",
                    models.CharField(
                        help_text="An organization category, e.g. committee",
                        max_length=128,
                        verbose_name="classification",
                        blank=True,
                    ),
                ),
                (
                    "dissolution_date",
                    models.CharField(
                        blank=True,
                        help_text="A date of dissolution",
                        max_length=10,
                        verbose_name="dissolution date",
                        validators=[
                            django.core.validators.RegexValidator(
                                regex=b"^[0-9]{4}(-[0-9]{2}){0,2}$",
                                message=b"dissolution date must follow the given pattern: ^[0-9]{4}(-[0-9]{2}){0,2}$",
                                code=b"invalid_dissolution_date",
                            )
                        ],
                    ),
                ),
                (
                    "founding_date",
                    models.CharField(
                        blank=True,
                        help_text="A date of founding",
                        max_length=10,
                        verbose_name="founding date",
                        validators=[
                            django.core.validators.RegexValidator(
                                regex=b"^[0-9]{4}(-[0-9]{2}){0,2}$",
                                message=b"founding date must follow the given pattern: ^[0-9]{4}(-[0-9]{2}){0,2}$",
                                code=b"invalid_founding_date",
                            )
                        ],
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        related_name="children",
                        blank=True,
                        to="popolo.Organization",
                        help_text="The organization that contains this organization",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="OtherName",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("object_id", models.PositiveIntegerField()),
                (
                    "start_date",
                    models.CharField(
                        validators=[
                            django.core.validators.RegexValidator(
                                regex=b"^[0-9]{4}(-[0-9]{2}){0,2}$",
                                message=b"Date has wrong format",
                            ),
                            popolo.behaviors.models.validate_partial_date,
                        ],
                        max_length=10,
                        blank=True,
                        help_text="The date when the validity of the item starts",
                        null=True,
                        verbose_name="start date",
                    ),
                ),
                (
                    "end_date",
                    models.CharField(
                        validators=[
                            django.core.validators.RegexValidator(
                                regex=b"^[0-9]{4}(-[0-9]{2}){0,2}$",
                                message=b"Date has wrong format",
                            ),
                            popolo.behaviors.models.validate_partial_date,
                        ],
                        max_length=10,
                        blank=True,
                        help_text="The date when the validity of the item ends",
                        null=True,
                        verbose_name="end date",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="An alternate or former name",
                        max_length=128,
                        verbose_name="name",
                    ),
                ),
                (
                    "note",
                    models.CharField(
                        help_text="A note, e.g. 'Birth name'",
                        max_length=256,
                        verbose_name="note",
                        blank=True,
                    ),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        to="contenttypes.ContentType", on_delete=models.CASCADE
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Person",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "start_date",
                    models.CharField(
                        validators=[
                            django.core.validators.RegexValidator(
                                regex=b"^[0-9]{4}(-[0-9]{2}){0,2}$",
                                message=b"Date has wrong format",
                            ),
                            popolo.behaviors.models.validate_partial_date,
                        ],
                        max_length=10,
                        blank=True,
                        help_text="The date when the validity of the item starts",
                        null=True,
                        verbose_name="start date",
                    ),
                ),
                (
                    "end_date",
                    models.CharField(
                        validators=[
                            django.core.validators.RegexValidator(
                                regex=b"^[0-9]{4}(-[0-9]{2}){0,2}$",
                                message=b"Date has wrong format",
                            ),
                            popolo.behaviors.models.validate_partial_date,
                        ],
                        max_length=10,
                        blank=True,
                        help_text="The date when the validity of the item ends",
                        null=True,
                        verbose_name="end date",
                    ),
                ),
                (
                    "created_at",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        verbose_name="creation time",
                        editable=False,
                    ),
                ),
                (
                    "updated_at",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        verbose_name="last modification time",
                        editable=False,
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="A person's preferred full name",
                        max_length=128,
                        verbose_name="name",
                    ),
                ),
                (
                    "family_name",
                    models.CharField(
                        help_text="One or more family names",
                        max_length=128,
                        verbose_name="family name",
                        blank=True,
                    ),
                ),
                (
                    "given_name",
                    models.CharField(
                        help_text="One or more primary given names",
                        max_length=128,
                        verbose_name="given name",
                        blank=True,
                    ),
                ),
                (
                    "additional_name",
                    models.CharField(
                        help_text="One or more secondary given names",
                        max_length=128,
                        verbose_name="additional name",
                        blank=True,
                    ),
                ),
                (
                    "honorific_prefix",
                    models.CharField(
                        help_text="One or more honorifics preceding a person's name",
                        max_length=128,
                        verbose_name="honorific prefix",
                        blank=True,
                    ),
                ),
                (
                    "honorific_suffix",
                    models.CharField(
                        help_text="One or more honorifics following a person's name",
                        max_length=128,
                        verbose_name="honorific suffix",
                        blank=True,
                    ),
                ),
                (
                    "patronymic_name",
                    models.CharField(
                        help_text="One or more patronymic names",
                        max_length=128,
                        verbose_name="patronymic name",
                        blank=True,
                    ),
                ),
                (
                    "sort_name",
                    models.CharField(
                        help_text="A name to use in an lexicographically ordered list",
                        max_length=128,
                        verbose_name="sort name",
                        blank=True,
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        help_text="A preferred email address",
                        max_length=254,
                        null=True,
                        verbose_name="email",
                        blank=True,
                    ),
                ),
                (
                    "gender",
                    models.CharField(
                        help_text="A gender",
                        max_length=128,
                        verbose_name="gender",
                        blank=True,
                    ),
                ),
                (
                    "birth_date",
                    models.CharField(
                        help_text="A date of birth",
                        max_length=10,
                        verbose_name="birth date",
                        blank=True,
                    ),
                ),
                (
                    "death_date",
                    models.CharField(
                        help_text="A date of death",
                        max_length=10,
                        verbose_name="death date",
                        blank=True,
                    ),
                ),
                (
                    "summary",
                    models.CharField(
                        help_text="A one-line account of a person's life",
                        max_length=512,
                        verbose_name="summary",
                        blank=True,
                    ),
                ),
                (
                    "biography",
                    models.TextField(
                        help_text="An extended account of a person's life",
                        verbose_name="biography",
                        blank=True,
                    ),
                ),
                (
                    "image",
                    models.URLField(
                        help_text="A URL of a head shot",
                        null=True,
                        verbose_name="image",
                        blank=True,
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Post",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "start_date",
                    models.CharField(
                        validators=[
                            django.core.validators.RegexValidator(
                                regex=b"^[0-9]{4}(-[0-9]{2}){0,2}$",
                                message=b"Date has wrong format",
                            ),
                            popolo.behaviors.models.validate_partial_date,
                        ],
                        max_length=10,
                        blank=True,
                        help_text="The date when the validity of the item starts",
                        null=True,
                        verbose_name="start date",
                    ),
                ),
                (
                    "end_date",
                    models.CharField(
                        validators=[
                            django.core.validators.RegexValidator(
                                regex=b"^[0-9]{4}(-[0-9]{2}){0,2}$",
                                message=b"Date has wrong format",
                            ),
                            popolo.behaviors.models.validate_partial_date,
                        ],
                        max_length=10,
                        blank=True,
                        help_text="The date when the validity of the item ends",
                        null=True,
                        verbose_name="end date",
                    ),
                ),
                (
                    "created_at",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        verbose_name="creation time",
                        editable=False,
                    ),
                ),
                (
                    "updated_at",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        verbose_name="last modification time",
                        editable=False,
                    ),
                ),
                (
                    "label",
                    models.CharField(
                        help_text="A label describing the post",
                        max_length=128,
                        verbose_name="label",
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        help_text="The function that the holder of the post fulfills",
                        max_length=128,
                        verbose_name="role",
                        blank=True,
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        related_name="posts",
                        to="popolo.Organization",
                        help_text="The organization in which the post is held",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Source",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("object_id", models.PositiveIntegerField()),
                ("url", models.URLField(help_text="A URL", verbose_name="url")),
                (
                    "note",
                    models.CharField(
                        help_text="A note, e.g. 'Parliament website'",
                        max_length=128,
                        verbose_name="note",
                        blank=True,
                    ),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        to="contenttypes.ContentType", on_delete=models.CASCADE
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.AddField(
            model_name="membership",
            name="on_behalf_of",
            field=models.ForeignKey(
                related_name="memberships_on_behalf_of",
                blank=True,
                to="popolo.Organization",
                help_text="The organization on whose behalf the person is a party to the relationship",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="membership",
            name="organization",
            field=models.ForeignKey(
                related_name="memberships",
                to="popolo.Organization",
                help_text="The organization that is a party to the relationship",
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="membership",
            name="person",
            field=models.ForeignKey(
                related_name="memberships",
                to="popolo.Person",
                help_text="The person who is a party to the relationship",
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="membership",
            name="post",
            field=models.ForeignKey(
                related_name="memberships",
                blank=True,
                to="popolo.Post",
                help_text="The post held by the person in the organization through this membership",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
    ]
