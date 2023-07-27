from django import template
from django.conf import settings
from django.contrib.humanize.templatetags.humanize import ordinal
from django.db.models import Prefetch
from django.utils.safestring import mark_safe
from popolo.models import Membership
from uk_results.models import CandidateResult

register = template.Library()


def get_candidacy(person, election):
    try:
        if "uk_results" in settings.INSTALLED_APPS:
            memberships_qs = person.memberships.prefetch_related(
                Prefetch(
                    "result",
                    CandidateResult.objects.select_related("result_set"),
                )
            )
        else:
            memberships_qs = person.memberships.all()
        return memberships_qs.get(ballot__election=election)
    except Membership.DoesNotExist:
        return None


def get_known_candidacy_prefix_and_suffix(candidacy):
    prefix = ""
    suffix = ""
    candidate_result = getattr(candidacy, "result", None)
    if candidate_result:
        # Then we're OK to display this result:
        suffix += "<br>"
        if candidacy.elected:
            suffix += '<span class="candidate-result-confirmed candidate-result-confirmed-elected">Elected!</span>'
        else:
            suffix += '<span class="candidate-result-confirmed candidate-result-confirmed-not-elected">Not elected</span>'
        suffix += ' <span class="vote-count">({} votes)</span>'.format(
            candidate_result.num_ballots
        )
        suffix += "<br>"
        suffix += " <span>{} / {} candidates </span>".format(
            ordinal(candidate_result.rank),
            candidacy.ballot.membership_set.count(),
        )
        suffix += "<br>"

    return prefix, suffix


@register.filter
def post_in_election(person, election):
    # FIXME: this is inefficient, but similar to the previous
    # implementation.
    candidacy = get_candidacy(person, election)
    if candidacy:
        link = '<a href="{cons_url}">{cons_name}</a>'.format(
            cons_url=candidacy.ballot.get_absolute_url(),
            cons_name=candidacy.ballot.post.short_label,
        )
        result = '<span class="constituency-value-standing-link">{}'.format(
            link
        )
        if candidacy.ballot.cancelled:
            result += " "
            result += candidacy.ballot.cancelled_status_html
        result += "</span>"
        result += ' <span class="party">{}</span>'.format(candidacy.party.name)
        if candidacy.party_list_position:
            result += ' <span class="party">List position {}</span>'.format(
                candidacy.party_list_position
            )
        prefix, suffix = get_known_candidacy_prefix_and_suffix(candidacy)
        result = prefix + result + suffix
        if candidacy.previous_party_affiliations.exists():
            for party in candidacy.previous_party_affiliations.all():
                result += '<ul class="previous-party"><li>Previous party affiliation: {}</li></ul>'.format(
                    party.name
                )

    else:
        if election in person.not_standing.all():
            if not election.in_past:
                result = (
                    '<span class="constituency-value-not-standing">%s</span>'
                    % "Not standing"
                )
            else:
                result = (
                    '<span class="constituency-value-not-standing">%s</span>'
                    % "Did not stand"
                )
        else:
            if not election.in_past:
                result = (
                    '<span class="constituency-value-unknown">%s</span>'
                    % "No information yet"
                )
            else:
                result = (
                    '<span class="constituency-not-standing">%s</span>'
                    % "Did not stand"
                )
    return mark_safe(result)


@register.filter
def election_decision_known(person, election):
    return person.get_elected(election) is not None


@register.filter
def was_elected(person, election):
    return bool(person.get_elected(election))
