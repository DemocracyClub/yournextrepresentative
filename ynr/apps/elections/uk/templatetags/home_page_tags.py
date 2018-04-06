import random

from django import template
from django.db.models import F
from django.conf import settings

from candidates.models import PostExtraElection
from elections.models import Election
from uk_results.models import CouncilElection
from tasks.models import PersonTask


register = template.Library()


def sopn_progress_by_election_slug_prefix(self, election_slug_prefix):
    election_qs = Election.objects.filter(
        slug__startswith=election_slug_prefix)
    return self.sopn_progress_by_election(election_qs)


def sopn_progress_by_election(election_qs):
    context = {}
    if not election_qs.exists():
        return context
    pee_qs = PostExtraElection.objects.filter(election__in=election_qs)
    context['posts_total'] = pee_qs.count()

    context['sopns_imported'] = pee_qs.filter(
        postextra__base__officialdocument__election=F('election'),
    ).count()
    context['sopns_imported_percent'] = round(
        float(context['sopns_imported']) /
        float(context['posts_total'])
        * 100)

    context['posts_lock_suggested'] = pee_qs.exclude(
        suggestedpostlock=None).count()
    context['posts_locked_suggested_percent'] = round(
        float(context['posts_lock_suggested']) /
        float(context['posts_total'])
        * 100)

    pee_qs = pee_qs.filter(candidates_locked=True)
    context['posts_locked'] = pee_qs.count()
    context['posts_locked_percent'] = round(
        float(context['posts_locked']) /
        float(context['posts_total'])
        * 100)

    return context


@register.inclusion_tag('link.html', takes_context=True)
def election_night_countil_control_progress(context):
    context['council_total'] = CouncilElection.objects.all().count()
    context['council_confirmed'] = CouncilElection.objects.filter(
        confirmed=True).count()

    if context['council_total']:
        context['council_election_percent'] = round(
            float(context['council_confirmed']) /
            float(context['council_total'])
            * 100)
    else:
        context['council_election_percent'] = 0


@register.inclusion_tag('includes/sopn_import_progress.html',
                        takes_context=True)
def sopn_import_progress(context):

    context['SHOW_SOPN_TRACKER'] = getattr(
        settings, 'SHOW_SOPN_TRACKER', False)
    if context['SHOW_SOPN_TRACKER']:
        context['sopn_tracker_election_name'] \
            = settings.SOPN_TRACKER_INFO['election_name']
        election_qs = Election.objects.filter(
            election_date=settings.SOPN_TRACKER_INFO['election_date'])
        context['sopn_progress'] = sopn_progress_by_election(
            election_qs=election_qs)
    return context


@register.inclusion_tag('includes/tasks.html', takes_context=True)
def person_tasks(context):
    task_count = PersonTask.objects.unfinished_tasks().count()
    if task_count > 0:
        random_offset = random.randrange(min(50, task_count))
        context['person_task'] = \
            PersonTask.objects.unfinished_tasks()[random_offset]
    else:
        person_task = None
    return context
