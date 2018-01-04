# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import importlib
from os.path import dirname, exists, join, realpath
import raven
import re
import yaml

from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS, LANGUAGES
from django.utils.translation import ugettext_lazy as _
from django.utils.translation.trans_real import to_locale

from mysite.helpers import mkdir_p

BASE_DIR = realpath(dirname(dirname(dirname(__file__))))

def get_conf(conf_file_leafname):
    full_filename = join(BASE_DIR, 'conf', conf_file_leafname)
    with open(full_filename) as f:
        return yaml.load(f)


def add_election_specific_settings(settings, full_election_app):
    election_settings_module = full_election_app + '.settings'
    elections_module = importlib.import_module(election_settings_module)

    # Set some required election-specific settings:
    for required_election_app_setting in (
            'SITE_OWNER',
            'COPYRIGHT_HOLDER',
    ):
        settings[required_election_app_setting] = \
            getattr(elections_module, required_election_app_setting)

    # Set optional election-specific settings:
    for optional_election_app_setting, default in (
            ('SITE_OWNER_URL', ''),
            ('AREAS_TO_ALWAYS_RETURN', []),
            ('IMAGE_PROXY_URL', ''),
    ):
        try:
            settings[optional_election_app_setting] = \
                getattr(elections_module, optional_election_app_setting)
        except AttributeError:
            settings[optional_election_app_setting] = default

    # Make sure there's a trailing slash at the end of base MapIt URL:
    settings['MAPIT_BASE_URL'] = \
        re.sub(r'/*$', '/', elections_module.MAPIT_BASE_URL)

    # Add any election-specific context processors:
    extra_context_processors = \
        getattr(elections_module, 'TEMPLATE_CONTEXT_PROCESSORS', ())
    settings['TEMPLATE_CONTEXT_PROCESSORS'] += extra_context_processors

    # Get any election-specific people whose pages might be
    # particularly subject to vandalism (e.g. party leaders):
    settings['PEOPLE_LIABLE_TO_VANDALISM'] = \
        getattr(elections_module, 'PEOPLE_LIABLE_TO_VANDALISM', set())

    # Add any election-specific INSTALLED_APPS:
    settings['INSTALLED_APPS'].extend(
        getattr(elections_module, 'INSTALLED_APPS', []))


def get_settings(conf_file_leafname, election_app=None, tests=False):
    conf = get_conf(conf_file_leafname)

    debug = bool(int(conf.get('STAGING')))

    # Get the requested ELECTION_APP:
    if election_app is None:
        election_app = conf['ELECTION_APP']
    election_app_fully_qualified = 'elections.' + election_app

    language_code = conf.get('LANGUAGE_CODE', 'en-gb')

    # Internationalization
    # https://docs.djangoproject.com/en/1.6/topics/i18n/
    locale_paths = [
        join(BASE_DIR, 'locale')
    ]
    # The code below sets LANGUAGES to only those we have translations
    # for, so at the time of writing that will be:
    #   [('en', 'English'), ('es-ar', 'Argentinian Spanish')]
    # whereas the default setting is a long list of languages which
    # includes:
    #   ('es', 'Spanish').
    # If someone's browser sends 'Accept-Language: es', that means that it
    # will be found in this list, but since there are no translations for 'es'
    # it'll fall back to LANGUAGE_CODE.  However, if there is no 'es' in
    # LANGUAGES, then Django will attempt to do a best match, so if
    # Accept-Language is 'es' then it will use the 'es-ar' translation.  We think
    # this is generally desirable (e.g. so someone can see YourNextMP in Spanish
    # if their browser asks for Spanish).
    languages = [
        l for l in LANGUAGES
        if exists(join(locale_paths[0], to_locale(l[0])))
    ]
    languages.append(('cy-gb', 'Welsh'))
    languages.append(('es-cr', 'Costa Rican Spanish'))

    # The language selection has been slightly complicated now that we
    # have two es- languages: es-ar and es-cr.  Chrome doesn't offer
    # Costa Rican Spanish as one of its language choices, so the best
    # you can do is choose 'Spanish - español'. (This might well be
    # the case in other browsers too.)  Since 'es-ar' comes first in
    # 'languages' after the preceding code, this means that someone
    # viewing the Costa Rica site with Chrome's preferred language set
    # to Spanish (i.e. with 'es' first in Accept-Language) will get
    # the Argentinian Spanish translations instead of Costa Rican
    # Spanish.  To get around this, look for the default language code
    # for the site, and if that's present, move it to the front of
    # 'languages'.  This should be generally helpful behaviour: the
    # default language code of the site should take precedence over
    # another language that happens to match based on the generic part
    # of the language code.
    language_code_index = next(
        (i for i, l in enumerate(languages) if l[0] == language_code),
        None
    )
    if language_code_index is not None:
        languages.insert(0, languages.pop(language_code_index))

    # Make sure the MEDIA_ROOT directory actually exists:
    media_root = conf.get('MEDIA_ROOT') or join(BASE_DIR, 'media')
    # Make sure that the MEDIA_ROOT and subdirectory for archived CSV
    # files exist:
    mkdir_p(join(media_root, 'csv-archives'))

    # Database
    # https://docs.djangoproject.com/en/1.6/ref/settings/#databases
    if conf.get('DATABASE_SYSTEM') == 'postgresql':
        databases = {
            'default': {
                'ENGINE':   'django.db.backends.postgresql_psycopg2',
                'NAME':     conf.get('YNMP_DB_NAME'),
                'USER':     conf.get('YNMP_DB_USER'),
                'PASSWORD': conf.get('YNMP_DB_PASS'),
                'HOST':     conf.get('YNMP_DB_HOST'),
                'PORT':     conf.get('YNMP_DB_PORT'),
                # Note that there are various comments on the web
                # suggesting that settings CONN_MAX_AGE != 0 is a bad
                # idea when eventlet or gevent workers are being used.
                'CONN_MAX_AGE': 0 if debug else 60,
            }
        }
    else:
        databases = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': join(BASE_DIR, 'db.sqlite3'),
            }
        }

    # Setup caches depending on DEBUG:
    if debug:
        cache = {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}
        cache_thumbnails = {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}
    else:
        cache = {
            'TIMEOUT': None, # cache keys never expire; we invalidate them
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': '127.0.0.1:11211',
            'KEY_PREFIX': databases['default']['NAME'],
        }
        cache_thumbnails = {
            'TIMEOUT': 60 * 60 * 24 * 2, # expire after two days
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': '127.0.0.1:11211',
            'KEY_PREFIX': databases['default']['NAME'] + "-thumbnails",
        }

    # Create a dictionary with these settings and other simpler ones:
    result = {
        'BASE_DIR': BASE_DIR,
        'ALLOWED_HOSTS': conf.get('ALLOWED_HOSTS'),
        'DEBUG': debug,
        'RUNNING_TESTS': tests,

        # Google analytics settings:
        'GOOGLE_ANALYTICS_ACCOUNT': conf.get('GOOGLE_ANALYTICS_ACCOUNT'),
        'USE_UNIVERSAL_ANALYTICS': conf.get('USE_UNIVERSAL_ANALYTICS', True),

        # The Twitter account referenced in the Twitter card data:
        'TWITTER_USERNAME': conf.get('TWITTER_USERNAME', ''),

        # The email address which is made public on the site for sending
        # support email to:
        'SUPPORT_EMAIL': conf['SUPPORT_EMAIL'],

        # Email addresses that error emails are sent to when DEBUG = False
        'ADMINS': conf['ADMINS'],

        # The From: address for all emails except error emails
        'DEFAULT_FROM_EMAIL': conf['DEFAULT_FROM_EMAIL'],

        # The From: address for error emails
        'SERVER_EMAIL': conf['SERVER_EMAIL'],

        # SECURITY WARNING: keep the secret key used in production secret!
        'SECRET_KEY': conf['SECRET_KEY'],

        'TEMPLATE_DEBUG': True,
        'TEMPLATE_DIRS': (
            join(BASE_DIR, 'mysite', 'templates'),
        ),
        'TEMPLATE_CONTEXT_PROCESSORS': TEMPLATE_CONTEXT_PROCESSORS + (
            # Required by allauth template tags
            "django.core.context_processors.request",
            "django.contrib.messages.context_processors.messages",
            "mysite.context_processors.add_settings",
            "mysite.context_processors.election_date",
            "mysite.context_processors.add_group_permissions",
            "mysite.context_processors.add_notification_data",
            "mysite.context_processors.locale",
            "mysite.context_processors.add_site",
        ),

        'ELECTION_APP': election_app,
        'ELECTION_APP_FULLY_QUALIFIED': election_app_fully_qualified,

        # The Django applications in use:
        'INSTALLED_APPS': [
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.humanize',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'django.contrib.sites',
            'django_nose',
            'django_extensions',
            'pipeline',
            'statici18n',
            'sorl.thumbnail',
            'rest_framework',
            'rest_framework.authtoken',
            'images',
            'haystack',
            'elections',
            'popolo',
            election_app_fully_qualified,
            'candidates',
            'tasks',
            'cached_counts',
            'moderation_queue',
            'auth_helpers',
            'debug_toolbar',
            'template_timings_panel',
            'official_documents',
            'results',
            'notifications',
            'allauth',
            'allauth.account',
            'allauth.socialaccount',
            'allauth.socialaccount.providers.google',
            'allauth.socialaccount.providers.facebook',
            'allauth.socialaccount.providers.twitter',
            'corsheaders',
            'crispy_forms',
            'markdown_deux',
            'raven.contrib.django.raven_compat',
        ],

        'SITE_ID': 1,

        'MIDDLEWARE_CLASSES': (
            'debug_toolbar.middleware.DebugToolbarMiddleware',
            'corsheaders.middleware.CorsMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.locale.LocaleMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'candidates.middleware.LogoutDisabledUsersMiddleware',
            'candidates.middleware.CopyrightAssignmentMiddleware',
            'candidates.middleware.DisallowedUpdateMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
            'candidates.middleware.DisableCachingForAuthenticatedUsers',
        ),

        # django-allauth settings:
        'AUTHENTICATION_BACKENDS': (
            # Needed to login by username in Django admin, regardless of `allauth`
            "django.contrib.auth.backends.ModelBackend",
            # `allauth` specific authentication methods, such as login by e-mail
            "allauth.account.auth_backends.AuthenticationBackend",
        ),
        'SOCIALACCOUNT_PROVIDERS': {
            'google': {'SCOPE': ['https://www.googleapis.com/auth/userinfo.profile'],
                       'AUTH_PARAMS': {'access_type': 'online'}},
            'facebook': {'SCOPE': ['email',]},
        },
        'LOGIN_REDIRECT_URL': '/',
        'ACCOUNT_AUTHENTICATION_METHOD': 'username_email',
        'ACCOUNT_EMAIL_VERIFICATION': 'mandatory',
        'ACCOUNT_EMAIL_REQUIRED': True,
        'ACCOUNT_FORMS': {
            'login': 'mysite.forms.CustomLoginForm',
            'signup': 'mysite.forms.CustomSignupForm',
        },
        'ACCOUNT_USERNAME_REQUIRED': True,
        'ACCOUNT_USERNAME_VALIDATORS': 'mysite.helpers.allauth_validators',
        'SOCIALACCOUNT_AUTO_SIGNUP': True,

        'ROOT_URLCONF': 'mysite.urls',
        'WSGI_APPLICATION': 'mysite.wsgi.application',

        # Django Debug Toolbar settings:
        'DEBUG_TOOLBAR_PATCH_SETTINGS': False,
        'DEBUG_TOOLBAR_PANELS': [
            'debug_toolbar.panels.versions.VersionsPanel',
            'debug_toolbar.panels.timer.TimerPanel',
            'debug_toolbar.panels.settings.SettingsPanel',
            'debug_toolbar.panels.headers.HeadersPanel',
            'debug_toolbar.panels.request.RequestPanel',
            'debug_toolbar.panels.sql.SQLPanel',
            'debug_toolbar.panels.staticfiles.StaticFilesPanel',
            'debug_toolbar.panels.templates.TemplatesPanel',
            'debug_toolbar.panels.cache.CachePanel',
            'debug_toolbar.panels.signals.SignalsPanel',
            'debug_toolbar.panels.logging.LoggingPanel',
            'debug_toolbar.panels.redirects.RedirectsPanel',
            'template_timings_panel.panels.TemplateTimings.TemplateTimings',
        ],
        'INTERNAL_IPS': ['127.0.0.1'],

        # Language settings (calculated above):
        'LOCALE_PATHS': locale_paths,
        'LANGUAGES': languages,
        'LANGUAGE_CODE': language_code,
        'TIME_ZONE': conf.get('TIME_ZONE', 'Europe/London'),
        'USE_I18N': True,
        'USE_L10N': True,
        'USE_TZ': True,
        'DD_MM_DATE_FORMAT_PREFERRED': conf.get('DD_MM_DATE_FORMAT_PREFERRED', True),

        # The media and static file settings:
        'MEDIA_ROOT': media_root,
        'MEDIA_URL': '/media/',

        # Settings for staticfiles and Django pipeline:
        'STATIC_URL': '/static/',
        'STATIC_ROOT': join(BASE_DIR, 'static'),
        'STATICI18N_ROOT': join(BASE_DIR, 'mysite', 'static'),
        'STATICFILES_DIRS': (
            join(BASE_DIR, 'mysite', 'static'),
        ),
        'STATICFILES_FINDERS': (
            'django.contrib.staticfiles.finders.FileSystemFinder',
            'django.contrib.staticfiles.finders.AppDirectoriesFinder',
            'pipeline.finders.PipelineFinder',
        ),
        'PIPELINE': {
            'STYLESHEETS': {
                'image-review': {
                    'source_filenames': (
                        'moderation_queue/css/jquery.Jcrop.css',
                        'moderation_queue/css/crop.scss',
                    ),
                    'output_filename': 'css/image-review.css',
                },
                'official_documents': {
                    'source_filenames': (
                        'official_documents/css/official_documents.scss',
                    ),
                    'output_filename': 'css/official_documents.css',
                },
                'bulk_adding': {
                    'source_filenames': (
                        'bulk_adding/css/bulk.scss',
                    ),
                    'output_filename': 'css/bulk_adding.css',
                },
                'all': {
                    'source_filenames': (
                        'candidates/style.scss',
                        'cached_counts/style.scss',
                        'select2/select2.css',
                        'jquery/jquery-ui.css',
                        'jquery/jquery-ui.structure.css',
                        'jquery/jquery-ui.theme.css',
                        'moderation_queue/css/photo-upload.scss',
                    ),
                    'output_filename': 'css/all.css',
                }
            },
            'JAVASCRIPT': {
                'image-review': {
                    'source_filenames': (
                        'moderation_queue/js/jquery.color.js',
                        'moderation_queue/js/jquery.Jcrop.js',
                        'moderation_queue/js/crop.js',
                    ),
                    'output_filename': 'js/image-review.js',
                },
                'bulk_adding': {
                    'source_filenames': (
                        'bulk_adding/js/bulk.js',
                    ),
                    'output_filename': 'js/bulk_adding.js',
                },
                'all': {
                    'source_filenames': (
                        'jquery/jquery-1.11.1.js',
                        'jquery/jquery-ui.js',
                        'foundation/js/foundation/foundation.js',
                        'foundation/js/foundation/foundation.equalizer.js',
                        'foundation/js/foundation/foundation.dropdown.js',
                        'foundation/js/foundation/foundation.tooltip.js',
                        'foundation/js/foundation/foundation.offcanvas.js',
                        'foundation/js/foundation/foundation.accordion.js',
                        'foundation/js/foundation/foundation.joyride.js',
                        'foundation/js/foundation/foundation.alert.js',
                        'foundation/js/foundation/foundation.topbar.js',
                        'foundation/js/foundation/foundation.reveal.js',
                        'foundation/js/foundation/foundation.slider.js',
                        'foundation/js/foundation/foundation.magellan.js',
                        'foundation/js/foundation/foundation.clearing.js',
                        'foundation/js/foundation/foundation.orbit.js',
                        'foundation/js/foundation/foundation.interchange.js',
                        'foundation/js/foundation/foundation.abide.js',
                        'foundation/js/foundation/foundation.tab.js',
                        'select2/select2.js',
                        'js/constituency.js',
                        'js/person_form.js',
                        'js/home_geolocation_form.js',
                        'js/versions.js',
                    ),
                    'output_filename': 'js/all.js'
                }
            },

            'COMPILERS': (
                'pipeline.compilers.sass.SASSCompiler',
            ),
            'SASS_BINARY': 'sassc',
            'CSS_COMPRESSOR': 'pipeline.compressors.yui.YUICompressor',
            'JS_COMPRESSOR': 'pipeline.compressors.yui.YUICompressor',
            # On some platforms this might be called "yuicompressor", so it may be
            # necessary to symlink it into your PATH as "yui-compressor".
            'YUI_BINARY': '/usr/bin/env yui-compressor',
        },


        'TEST_RUNNER': 'django_nose.NoseTestSuiteRunner',

        'SOURCE_HINTS': _(
            u"Please don't quote third-party candidate sites \u2014 "
            u"we prefer URLs of news stories or official candidate pages."
        ),

        # By default, cache successful results from MapIt for a day
        'MAPIT_CACHE_SECONDS': 86400,
        'DATABASES': databases,
        'CACHES': {
            'default': cache,
            'thumbnails': cache_thumbnails,
        },

        # sorl-thumbnail settings:
        'THUMBNAIL_CACHE': 'thumbnails',
        'THUMBNAIL_DEBUG': debug,

        # Settings for restricting user activity to reduce abuse:
        'RESTRICT_RENAMES': conf.get('RESTRICT_RENAMES'),
        'EDITS_ALLOWED': conf.get('EDITS_ALLOWED', True),
        'SHOW_BANNER': conf.get('SHOW_BANNER', False),

        # A bearer token for the Twitter API for mapping between
        # Twitter usernames and IDs.
        'TWITTER_APP_ONLY_BEARER_TOKEN': conf.get('TWITTER_APP_ONLY_BEARER_TOKEN'),

        # Django Rest Framework settings:
        'REST_FRAMEWORK': {
            'DEFAULT_PERMISSION_CLASSES': ('candidates.api_permissions.ReadOnly',),
            'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
            'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend',),
            'DEFAULT_RENDERER_CLASSES': (
                'rest_framework.renderers.JSONRenderer',
                'rest_framework_jsonp.renderers.JSONPRenderer',
                'rest_framework.renderers.BrowsableAPIRenderer',
            ),
            'PAGE_SIZE': 10,
        },

        # allow attaching extra data to notifications:
        'NOTIFICATIONS_USE_JSONFIELD': True,

        'HAYSTACK_SIGNAL_PROCESSOR': 'haystack.signals.RealtimeSignalProcessor',

        'HAYSTACK_CONNECTIONS': {
            'default': {
                'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
                'URL': 'http://127.0.0.1:9200/',
                'INDEX_NAME': '{0}_{1}'.format(conf.get('YNMP_DB_NAME'), conf.get('YNMP_DB_HOST')),
            },
        },

        # CORS config
        'CORS_ORIGIN_ALLOW_ALL': True,
        'CORS_URLS_REGEX': r'^/(api|upcoming-elections)/.*$',
        'CORS_ALLOW_METHODS': (
            'GET',
            'OPTIONS',
        ),

        'MARKDOWN_DEUX_STYLES': {
            "default": {
                "extras": {
                    "code-friendly": None,
                    "fenced-code-blocks": None,
                },
                "safe_mode": "escape",
            },
        }
    }
    if not conf.get('NEW_ACCOUNTS_ALLOWED', True):
        result['ACCOUNT_ADAPTER'] = \
            'mysite.account_adapter.NoNewUsersAccountAdapter'
    result['CANDIDATES_REQUIRED_FOR_WEIGHTED_PARTY_LIST'] = \
        conf.get('CANDIDATES_REQUIRED_FOR_WEIGHTED_PARTY_LIST', 20)
    result['HOIST_ELECTED_CANDIDATES'] = \
        conf.get('HOIST_ELECTED_CANDIDATES', True)
    if tests:
        result['NOSE_ARGS'] = [
            '--nocapture',
            '--with-yanc',
            # There are problems with OpenCV on Travis, so don't even try to
            # import moderation_queue/faces.py
            '--ignore-files=faces',
        ]
        if election_app == 'example':
            result['NOSE_ARGS'].append('--with-doctest')
    else:
        # If we're not testing, use PipelineCachedStorage
        result['STATICFILES_STORAGE'] = \
            'pipeline.storage.PipelineCachedStorage'
    if conf.get('NGINX_SSL'):
        result['SECURE_PROXY_SSL_HEADER'] = ('HTTP_X_FORWARDED_PROTO', 'https')
        result['ACCOUNT_DEFAULT_HTTP_PROTOCOL'] = 'https'

    # optionally configure the raven client for sentry.io
    if conf.get('RAVEN_DSN'):
        result['RAVEN_CONFIG'] = {'dsn': conf.get('RAVEN_DSN')}

    add_election_specific_settings(result, election_app_fully_qualified)

    result['RESULTS_FEATURE_ACTIVE'] = True
    result['CAN_EDIT_ELECTIONS'] = conf.get('CAN_EDIT_ELECTIONS', True)

    result['DATE_FORMAT'] = conf.get('DATE_FORMAT', "jS E Y")

    return result
