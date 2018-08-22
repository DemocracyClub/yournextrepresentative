from contextlib import contextmanager

from django.conf import settings


@contextmanager
def default_additional_merge_actions(primary_person, secondary_person):
    yield


# This is actually taken from Pombola's country-specific code package
# in pombola/country/__init__.py. You should add to this list anything
# country-specific you want to be available through an import from
# candidates.election_specific

imports_and_defaults = (
    ("EXTRA_CSV_ROW_FIELDS", []),
    ("shorten_post_label", lambda post_label: post_label),
    ("get_extra_csv_values", lambda person, election, post: {}),
    ("additional_merge_actions", default_additional_merge_actions),
)

# Note that one could do this without the dynamic import and use of
# globals() by switching on country names and importing * from each
# country specific module, as MapIt does. [1] I slightly prefer the
# version here since you can explicitly list the names to be imported,
# and provide a default value.
#
# [1] https://github.com/mysociety/mapit/blob/master/mapit/countries/__init__.py

for name_to_import, default_value in imports_and_defaults:
    value = default_value
    if settings.ELECTION_APP:
        try:
            value = getattr(
                __import__(
                    settings.ELECTION_APP_FULLY_QUALIFIED + ".lib",
                    fromlist=[name_to_import],
                ),
                name_to_import,
            )
        except (ImportError, AttributeError):
            pass
    globals()[name_to_import] = value
