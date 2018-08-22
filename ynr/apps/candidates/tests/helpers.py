import difflib
import json
from tempfile import mkdtemp
import shutil

import sys

from compat import text_type

from django.test import TestCase, override_settings
from django.conf import settings


def p(*args):
    """A helper for printing to stderr"""
    print(file=sys.stderr, *args)


def deep_cast_to_unicode(obj):
    """
    >>> deep_cast_to_unicode(b'Foo') == u'Foo'
    True
    >>> deep_cast_to_unicode({b'x': b'y'}) == {u'x': u'y'}
    True
    >>> (deep_cast_to_unicode([b'a', b'b', u'c', {b'x': b'y'}]) ==
         [u'a', u'b', u'c', {u'x': u'y'}])
    True
    """
    if isinstance(obj, text_type):
        return obj
    elif isinstance(obj, bytes):
        return obj.decode("utf-8")
    elif isinstance(obj, dict):
        return {
            deep_cast_to_unicode(k): deep_cast_to_unicode(v)
            for k, v in obj.items()
        }
    elif isinstance(obj, list):
        return [deep_cast_to_unicode(k) for k in obj]
    elif obj is None:
        return None
    return repr(obj)


def equal_arg(arg1, arg2):
    """Return True if the args are equal, False otherwise

    If the arguments aren't equal under ==, return True, otherwise
    return False and try to output to stderr a diff of the
    pretty-printed objects."""

    if arg1 == arg2:
        return True

    # This is more or less taken from assertDictEqual in
    # django/utils/unittest/case.py:
    args1_lines = json.dumps(
        deep_cast_to_unicode(arg1), indent=4, sort_keys=True
    ).splitlines()
    args2_lines = json.dumps(
        deep_cast_to_unicode(arg2), indent=4, sort_keys=True
    ).splitlines()
    diff = difflib.ndiff(args1_lines, args2_lines)

    p("Found the following differences: ====================================")
    for line in diff:
        p(line)
    p("=====================================================================")

    return False


def equal_call_args(args1, args2):
    """Return True if two sequences of arguments are equal

    Otherwise return False and output a diff of the first non-equal
    arguments to stderr."""
    if len(args1) != len(args2):
        message = "The argument lists were different lengths: {0} and {1}"
        p(message.format(len(args1), len(args2)))

    for i, arg1 in enumerate(args1):
        if not equal_arg(arg1, args2[i]):
            return False

    return True


@override_settings(
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage",
    DEFAULT_FILE_STORAGE="django.core.files.storage.FileSystemStorage",
    MEDIA_ROOT=mkdtemp(),
)
class TmpMediaRootMixin(TestCase):
    """
    Makes a new MEDIA_ROOT at a temporary location and cleans it up after.

    This mixin also ensures that reasonable storage backends are used for
    testing, ensuring that any local settings aren't used. This is important
    because we don't want to test deleting remote production files just
    because that's what's in the user's settings.

    """

    def tearDown(self):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
