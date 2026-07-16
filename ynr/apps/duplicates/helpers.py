from django.db.models import Q
from duplicates.models import DuplicateSuggestion


def get_previous_rejections(pairs):
    """
    Given a list of (person_id, other_person_id) tuples
    (where person_id is always the lower of the two IDs)
    returns a dict mapping each tuple to a
    list of rejected DuplicateSuggestion instances,
    ordered by modification date.
    """
    if not pairs:
        return {}

    pairs_q = Q()
    for person_id, other_person_id in pairs:
        pairs_q |= Q(person_id=person_id, other_person_id=other_person_id)

    rejections = (
        DuplicateSuggestion.objects.rejected()
        .filter(pairs_q)
        .select_related("user")
        .order_by("modified")
    )

    result = {pair: [] for pair in pairs}
    for rejection in rejections:
        key = (rejection.person_id, rejection.other_person_id)
        if key in result:
            result[key].append(rejection)

    return result
