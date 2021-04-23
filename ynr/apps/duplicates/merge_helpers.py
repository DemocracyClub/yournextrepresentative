"""
Helpers for updating DuplicateSuggestion models after merging.
"""

from .models import DuplicateSuggestion


def alter_duplicate_suggestion_post_merge(source_person, dest_person):

    # Case 1, the primary and secondary people are the same as the DS
    # Because the secondary person is about to get deleted, we need to delete
    # this DuplicateSuggestion too.
    DuplicateSuggestion.objects.for_both_people(
        source_person, dest_person
    ).delete()

    # Case 2: The secondary person has a DS but we are merging it in to someone
    # else in this case we need to update the ID

    # Any suggestions where the 'person' (the destination of a suggestion) is the
    # source of this merge (the object we area bout to delete), update to change
    # the 'person' to the destination of this merge
    DuplicateSuggestion.objects.filter(person=source_person).update(
        person=dest_person
    )
    # Any suggestions where the 'other_person' (the source of another suggestion)
    # is the destination of this merge, update the source to be the destination
    # of this merge
    # we need to loop through and save individually to make sure that the
    # people are sorted correctly
    for suggestion in DuplicateSuggestion.objects.filter(
        other_person=source_person
    ):
        suggestion.other_person = dest_person
        suggestion.save()
