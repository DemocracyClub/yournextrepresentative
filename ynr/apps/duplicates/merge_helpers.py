"""
Helpers for updating DuplicateSuggestion models after merging.
"""

from .models import DuplicateSuggestion


def alter_duplicate_suggestion_post_merge(primary, secondary):

    # Case 1, the primary and secondary people are the same as the DS
    # Because the secondary person is about to get deleted, we need to delete
    # this DuplicateSuggestion too.
    DuplicateSuggestion.objects.for_both_people(primary, secondary).delete()

    # Case 2: The secondary person has a DS but we are merging it in to someone
    # else in this case we need to update the ID
    DuplicateSuggestion.objects.filter(person=secondary).update(person=primary)
    DuplicateSuggestion.objects.filter(other_person=secondary).update(
        other_person=primary
    )
