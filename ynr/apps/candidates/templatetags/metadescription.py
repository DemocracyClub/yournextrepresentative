import re

from django import template
from django.contrib.sites.models import Site

register = template.Library()


@register.simple_tag
def metadescription(person, last_candidacy, today):
    if last_candidacy:
        election = last_candidacy.post_election.election
        last_party_name = format_party_name(last_candidacy.party.name)
        args = {
            "election": election.name,
            "name": person.name,
            "party": last_party_name,
            "post": last_candidacy.post.label,
        }
        if is_post_election(election, today):
            if last_party_name == "Independent" % args:
                output = (
                    "%(name)s stood as an independent candidate in %(post)s in %(election)s"
                ) % args
            else:
                output = (
                    "%(name)s stood for %(party)s in %(post)s in %(election)s"
                ) % args
        else:
            if last_party_name == "Independent" % args:
                output = (
                    "%(name)s is standing as an independent candidate in %(post)s in %(election)s"
                    % args
                )
            else:
                output = (
                    "%(name)s is standing for %(party)s in %(post)s in %(election)s"
                    % args
                )
    else:
        output = person.name

    output += " – " + "find out more on {site_name}".format(
        site_name=Site.objects.get_current().name
    )
    return output


def is_post_election(election, today):
    return today > election.election_date


def format_party_name(party_name):
    party_name = party_name.strip()
    # otherwise we end up with "the Independent", which sounds like
    # they're standing for a newspaper
    if party_name != "Independent":
        party_name = re.sub("^The ", "the ", party_name)
        party_words = party_name.split()
        if party_words[0] != "the":
            return "the %s" % party_name
    return party_name
