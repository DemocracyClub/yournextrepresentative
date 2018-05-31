from __future__ import unicode_literals

from django.views.generic import TemplateView, UpdateView

from popolo.models import Membership, ContactDetail
from tasks.models import PersonTask


class TaskHomeView(TemplateView):
    template_name = "tasks/tasks_home.html"

class IncompleteFieldView(TemplateView):
    page_kwarg = 'page'
    template_name = 'tasks/field.html'

    def get_template_names(self):
        return [
            'tasks/field_%s.html' % self.kwargs['field'],
            'tasks/field.html'
        ]

    def get_context_data(self, **kwargs):
        context = super(IncompleteFieldView,
            self).get_context_data(**kwargs)
        all_results = Membership.objects \
            .select_related('person', 'post', 'person__extra', 'post__extra', 'on_behalf_of') \
            .filter(
                role='Candidate',
                post_election__election__current=True,
            )

        filtered_results = self.get_results(all_results)

        twitter_names = ContactDetail.objects.filter(contact_type='twitter').all()
        person_to_twitter = {}
        for twitter in twitter_names:
            person_to_twitter[twitter.object_id] = twitter.value

        """
        This is required as there's not a sensible way to include the
        twitter details in the query so we need to do two queries and then
        merge the results here.
        """
        result_context = []
        for result in filtered_results.all():
            details = {
                'person': {
                    'id': result.person_id,
                    'name': result.person.name
                },
                'party': {
                    'name': result.on_behalf_of.name
                },
                'post': {
                    'name': result.post.extra.short_label
                }
            }
            if person_to_twitter.get(result.person_id, None) is not None:
                details['twitter'] = person_to_twitter[result.person_id]
            result_context.append(details)

        context['results'] = result_context
        context['results_count'] = filtered_results.count()

        candidates_count = all_results.count()
        if candidates_count == 0:
            context['percent_empty'] = 0
        else:
            context['percent_empty'] = \
                (100 * context['results_count'] / float(candidates_count))
        context['candidates_count'] = candidates_count

        return context

    def get_results(self, results):
        field = self.kwargs.get('field')

        if field == "twitter" or field == 'facebook' or field == 'phone':
            filtered_results = results.exclude(person__contact_details__contact_type=field)
        else:
            field_spec = "person__{0}__isnull".format(field)
            args = {field_spec: True}
            filtered_results = results.filter(**args)

        return filtered_results


class CouldntFindFieldView(UpdateView):
    model = PersonTask
    fields = ('person', 'task_field')
    success_url = "/"

    def get_object(self, queryset=None):
        return PersonTask.objects.get(
            person_id=self.kwargs['pk'],
            task_field=self.request.POST.get('task_field')
        )

    def form_valid(self, form):
        task = form.save()
        task.log_not_found()
        return super(CouldntFindFieldView, self).form_valid(form)

