from __future__ import unicode_literals

from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.text import slugify
from .models import ResultEvent

class ResultEventAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'election',
        'user',
        'created',
        'winner_link',
        'old_post_id',
        'old_post_name',
        'post_link',
        'source',
    )
    search_fields = (
        'id',
        'election__name',
        'user__username',
        'winner__name',
        'old_post_id',
        'old_post_name',
        'source',
    )
    ordering = ('-created',)

    def get_queryset(self, request):
        qs = super(ResultEventAdmin, self).get_queryset(request)
        return qs.select_related('user', 'winner', 'post__extra', 'winner_party__extra', 'election')

    def winner_link(self, o):
        url = reverse(
            'person-view',
            kwargs={
                'person_id': o.winner.id,
                'ignored_slug': slugify(o.winner.name),
            }
        )
        return '<a href="{}">{}</a>'.format(
            url,
            o.winner.name,
        )
    winner_link.allow_tags = True

    def post_link(self, o):
        if o.post:
            url = reverse(
                'constituency',
                kwargs={
                    'election': o.election.slug,
                    'post_id': o.post.extra.slug,
                    'ignored_slug': slugify(o.post.extra.short_label),
                }
            )
            return '<a href="{}">{}</a>'.format(
                url,
                o.post.extra.short_label,
            )
        else:
            # There is still data in the database for some posts that
            # were deleted and never recreated, so we can't create a
            # link for them.
            return ''
    post_link.allow_tags = True

admin.site.register(ResultEvent, ResultEventAdmin)
