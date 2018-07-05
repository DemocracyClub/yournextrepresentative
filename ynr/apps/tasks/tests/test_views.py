from django.test import TestCase

from candidates.tests.factories import (
    ElectionFactory, MembershipFactory,
    ParliamentaryChamberFactory, PartyFactory, PartyExtraFactory,
    PersonExtraFactory, PostExtraFactory
)
from candidates.tests.uk_examples import UK2015ExamplesMixin


class TestFieldView(UK2015ExamplesMixin, TestCase):

    def setUp(self):
        super(TestFieldView, self).setUp()

        person_extra = PersonExtraFactory.create(
            base__id='2009',
            base__name='Tessa Jowell'
        )

        MembershipFactory.create(
            person=person_extra.base,
            post=self.dulwich_post_extra.base,
            on_behalf_of=self.green_party_extra.base,
            post_election=self.dulwich_post_extra_pee
        )

        person_extra = PersonExtraFactory.create(
            base__id='2010',
            base__name='Andrew Smith',
            base__email='andrew@example.com',
        )

        MembershipFactory.create(
            person=person_extra.base,
            post=self.dulwich_post_extra.base,
            on_behalf_of=self.green_party_extra.base,
            post_election=self.dulwich_post_extra_pee
        )

    def test_context_data(self):
        url = '/tasks/email/'

        response = self.client.get(url)
        self.assertEqual(response.context['field'], 'email')
        self.assertEqual(response.context['candidates_count'], 2)
        self.assertEqual(response.context['results_count'], 1)

        self.assertContains(response, 'Tessa Jowell')

    def test_template_used(self):
        response = self.client.get('/tasks/email/')
        self.assertTemplateUsed(response, 'tasks/field.html')
