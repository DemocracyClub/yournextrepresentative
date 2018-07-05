# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields
import django.core.validators
import popolo.behaviors.models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('popolo', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Area',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField(null=True, blank=True)),
                ('start_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item starts', null=True, verbose_name='start date')),
                ('end_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item ends', null=True, verbose_name='end date')),
                ('created_at', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='creation time', editable=False)),
                ('updated_at', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='last modification time', editable=False)),
                ('name', models.CharField(help_text='A primary name', max_length=256, verbose_name='name', blank=True)),
                ('identifier', models.CharField(help_text='An issued identifier', max_length=512, verbose_name='identifier', blank=True)),
                ('classification', models.CharField(help_text='An area category, e.g. city', max_length=512, verbose_name='identifier', blank=True)),
                ('geom', models.TextField(help_text='A geometry', null=True, verbose_name='geom', blank=True)),
                ('inhabitants', models.IntegerField(help_text='The total number of inhabitants', null=True, verbose_name='inhabitants', blank=True)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
                ('parent', models.ForeignKey(related_name='children', blank=True, to='popolo.Area', help_text='The area that contains this area', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AreaI18Name',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('area', models.ForeignKey(related_name='i18n_names', to='popolo.Area')),
            ],
            options={
                'verbose_name': 'I18N Name',
                'verbose_name_plural': 'I18N Names',
            },
        ),
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dbpedia_resource', models.CharField(help_text='DbPedia URI of the resource', unique=True, max_length=255)),
                ('iso639_1_code', models.CharField(max_length=2)),
                ('name', models.CharField(help_text='English name of the language', max_length=128)),
            ],
        ),
        migrations.AlterModelOptions(
            name='person',
            options={'verbose_name_plural': 'People'},
        ),
        migrations.AddField(
            model_name='organization',
            name='description',
            field=models.TextField(help_text='An extended description of an organization', verbose_name='biography', blank=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='image',
            field=models.URLField(help_text='A URL of an image, to identify the organization visually', null=True, verbose_name='image', blank=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='summary',
            field=models.CharField(help_text='A one-line description of an organization', max_length=1024, verbose_name='summary', blank=True),
        ),
        migrations.AddField(
            model_name='person',
            name='national_identity',
            field=models.CharField(help_text='A national identity', max_length=128, null=True, verbose_name='national identity', blank=True),
        ),
        migrations.AddField(
            model_name='post',
            name='other_label',
            field=models.CharField(help_text='An alternate label, such as an abbreviation', max_length=512, null=True, verbose_name='other label', blank=True),
        ),
        migrations.AlterField(
            model_name='contactdetail',
            name='contact_type',
            field=models.CharField(help_text="A type of medium, e.g. 'fax' or 'email'", max_length=12, verbose_name='type', choices=[(b'ADDRESS', 'Address'), (b'EMAIL', 'Email'), (b'URL', 'Url'), (b'MAIL', 'Snail mail'), (b'TWITTER', 'Twitter'), (b'FACEBOOK', 'Facebook'), (b'PHONE', 'Telephone'), (b'MOBILE', 'Mobile'), (b'TEXT', 'Text'), (b'VOICE', 'Voice'), (b'FAX', 'Fax'), (b'CELL', 'Cell'), (b'VIDEO', 'Video'), (b'PAGER', 'Pager'), (b'TEXTPHONE', 'Textphone')]),
        ),
        migrations.AlterField(
            model_name='contactdetail',
            name='content_type',
            field=models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True),
        ),
        migrations.AlterField(
            model_name='contactdetail',
            name='label',
            field=models.CharField(help_text='A human-readable label for the contact detail', max_length=512, verbose_name='label', blank=True),
        ),
        migrations.AlterField(
            model_name='contactdetail',
            name='note',
            field=models.CharField(help_text='A note, e.g. for grouping contact details by physical location', max_length=512, verbose_name='note', blank=True),
        ),
        migrations.AlterField(
            model_name='contactdetail',
            name='object_id',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='contactdetail',
            name='value',
            field=models.CharField(help_text='A value, e.g. a phone number or email address', max_length=512, verbose_name='value'),
        ),
        migrations.AlterField(
            model_name='identifier',
            name='content_type',
            field=models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True),
        ),
        migrations.AlterField(
            model_name='identifier',
            name='identifier',
            field=models.CharField(help_text='An issued identifier, e.g. a DUNS number', max_length=512, verbose_name='identifier'),
        ),
        migrations.AlterField(
            model_name='identifier',
            name='object_id',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='link',
            name='content_type',
            field=models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True),
        ),
        migrations.AlterField(
            model_name='link',
            name='note',
            field=models.CharField(help_text="A note, e.g. 'Wikipedia page'", max_length=512, verbose_name='note', blank=True),
        ),
        migrations.AlterField(
            model_name='link',
            name='object_id',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='link',
            name='url',
            field=models.URLField(help_text='A URL', max_length=350, verbose_name='url'),
        ),
        migrations.AlterField(
            model_name='membership',
            name='label',
            field=models.CharField(help_text='A label describing the membership', max_length=512, verbose_name='label', blank=True),
        ),
        migrations.AlterField(
            model_name='membership',
            name='organization',
            field=models.ForeignKey(related_name='memberships', blank=True, to='popolo.Organization', help_text='The organization that is a party to the relationship', null=True),
        ),
        migrations.AlterField(
            model_name='membership',
            name='role',
            field=models.CharField(help_text='The role that the person fulfills in the organization', max_length=512, verbose_name='role', blank=True),
        ),
        migrations.AlterField(
            model_name='organization',
            name='classification',
            field=models.CharField(help_text='An organization category, e.g. committee', max_length=512, verbose_name='classification', blank=True),
        ),
        migrations.AlterField(
            model_name='organization',
            name='dissolution_date',
            field=models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'dissolution date must follow the given pattern: ^[0-9]{4}(-[0-9]{2}){0,2}$', code=b'invalid_dissolution_date')], max_length=10, blank=True, help_text='A date of dissolution', null=True, verbose_name='dissolution date'),
        ),
        migrations.AlterField(
            model_name='organization',
            name='founding_date',
            field=models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'founding date must follow the given pattern: ^[0-9]{4}(-[0-9]{2}){0,2}$', code=b'invalid_founding_date')], max_length=10, blank=True, help_text='A date of founding', null=True, verbose_name='founding date'),
        ),
        migrations.AlterField(
            model_name='organization',
            name='name',
            field=models.CharField(help_text='A primary name, e.g. a legally recognized name', max_length=512, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='othername',
            name='content_type',
            field=models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True),
        ),
        migrations.AlterField(
            model_name='othername',
            name='name',
            field=models.CharField(help_text='An alternate or former name', max_length=512, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='othername',
            name='note',
            field=models.CharField(help_text="A note, e.g. 'Birth name'", max_length=1024, verbose_name='note', blank=True),
        ),
        migrations.AlterField(
            model_name='othername',
            name='object_id',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='person',
            name='name',
            field=models.CharField(help_text="A person's preferred full name", max_length=512, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='person',
            name='summary',
            field=models.CharField(help_text="A one-line account of a person's life", max_length=1024, verbose_name='summary', blank=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='label',
            field=models.CharField(help_text='A label describing the post', max_length=512, verbose_name='label', blank=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='role',
            field=models.CharField(help_text='The function that the holder of the post fulfills', max_length=512, verbose_name='role', blank=True),
        ),
        migrations.AlterField(
            model_name='source',
            name='content_type',
            field=models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True),
        ),
        migrations.AlterField(
            model_name='source',
            name='note',
            field=models.CharField(help_text="A note, e.g. 'Parliament website'", max_length=512, verbose_name='note', blank=True),
        ),
        migrations.AlterField(
            model_name='source',
            name='object_id',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='areai18name',
            name='language',
            field=models.ForeignKey(to='popolo.Language'),
        ),
        migrations.AddField(
            model_name='membership',
            name='area',
            field=models.ForeignKey(related_name='memberships', blank=True, to='popolo.Area', help_text='The geographic area to which the post is related', null=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='area',
            field=models.ForeignKey(related_name='organizations', blank=True, to='popolo.Area', help_text='The geographic area to which this organization is related', null=True),
        ),
        migrations.AddField(
            model_name='post',
            name='area',
            field=models.ForeignKey(related_name='posts', blank=True, to='popolo.Area', help_text='The geographic area to which the post is related', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='areai18name',
            unique_together={('area', 'language', 'name')},
        ),
    ]
