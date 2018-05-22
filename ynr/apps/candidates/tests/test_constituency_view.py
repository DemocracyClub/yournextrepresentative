from __future__ import unicode_literals

from django.utils.six import text_type
from django_webtest import WebTest

from .auth import TestUserMixin
from .dates import date_in_near_future
from .factories import (
    CandidacyExtraFactory, ElectionFactory, MembershipFactory,
    OrganizationExtraFactory, PersonExtraFactory, PostExtraFactory,
)
from .uk_examples import UK2015ExamplesMixin

from compat import BufferDictReader

from candidates.models import MembershipExtra, PersonExtra


class TestConstituencyDetailView(TestUserMixin, UK2015ExamplesMixin, WebTest):

    def setUp(self):
        super(TestConstituencyDetailView, self).setUp()
        person_extra = PersonExtraFactory.create(
            base__id='2009',
            base__name='Tessa Jowell'
        )
        dulwich_not_stand = PersonExtraFactory.create(
            base__id='4322',
            base__name='Helen Hayes'
        )
        CandidacyExtraFactory.create(
            base__person=person_extra.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base,
            post_election=self.dulwich_post_extra_pee,
        )
        MembershipFactory.create(
            person=person_extra.base,
            organization=self.labour_party_extra.base
        )

        winner_post_extra = self.edinburgh_east_post_extra

        edinburgh_candidate = PersonExtraFactory.create(
            base__id='818',
            base__name='Sheila Gilmore'
        )
        edinburgh_winner = PersonExtraFactory.create(
            base__id='5795',
            base__name='Tommy Sheppard'
        )
        edinburgh_may_stand = PersonExtraFactory.create(
            base__id='5163',
            base__name='Peter McColl'
        )

        CandidacyExtraFactory.create(
            base__person=dulwich_not_stand.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base,
            post_election=self.dulwich_post_extra_pee_earlier
        )
        dulwich_not_stand.not_standing.add(self.election)

        CandidacyExtraFactory.create(
            base__person=edinburgh_winner.base,
            base__post=winner_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base,
            elected=True,
            post_election=self.election.postextraelection_set.get(
                postextra=winner_post_extra
            )
        )

        CandidacyExtraFactory.create(
            base__person=edinburgh_candidate.base,
            base__post=winner_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base,
            post_election=self.dulwich_post_extra_pee,
        )
        MembershipFactory.create(
            person=edinburgh_candidate.base,
            organization=self.labour_party_extra.base
        )
        MembershipFactory.create(
            person=edinburgh_winner.base,
            organization=self.labour_party_extra.base
        )
        CandidacyExtraFactory.create(
            base__person=edinburgh_may_stand.base,
            base__post=winner_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base,
            post_election=self.earlier_election.postextraelection_set.get(
                postextra=winner_post_extra
            )
        )

    def test_any_constituency_page_without_login(self):
        # Just a smoke test for the moment:
        response = self.app.get('/election/2015/post/65808/dulwich-and-west-norwood')
        response.mustcontain('<a href="/person/2009/tessa-jowell" class="candidate-name">Tessa Jowell</a> <span class="party">Labour Party</span>')
        # There should be only one form ( person search ) on the page if you're not logged in:

        # even though there is only one form on the page the list has
        # two entries - one for the numeric identifier and one for the id
        self.assertEqual(2, len(response.forms))
        self.assertEqual(response.forms[0].id, 'person_search_header')

    def test_any_constituency_page(self):
        # Just a smoke test for the moment:
        response = self.app.get(
            '/election/2015/post/65808/dulwich-and-west-norwood',
            user=self.user
        )
        response.mustcontain('<a href="/person/2009/tessa-jowell" class="candidate-name">Tessa Jowell</a> <span class="party">Labour Party</span>')
        form = response.forms['new-candidate-form']
        self.assertTrue(form)
        response.mustcontain(no='Unset the current winners')

    def test_constituency_with_no_winner_record_results_user(self):
        response = self.app.get(
            '/election/2015/post/65808/dulwich-and-west-norwood',
            user=self.user_who_can_record_results
        )
        response.mustcontain(no='Unset the current winners')

    def test_any_constituency_csv(self):
        response = self.app.get(
            '/election/2015/post/65808/dulwich-and-west-norwood.csv',
        )
        row_dicts = [row for row in BufferDictReader(response.content)]
        self.assertEqual(1, len(row_dicts))
        self.assertEqual(
            row_dicts[0],
            {
                'birth_date': '',
                'elected': '',
                'election': '2015',
                'election_current': 'True',
                'election_date': text_type(date_in_near_future),
                'email': '',
                'facebook_page_url': '',
                'facebook_personal_url': '',
                'favourite_biscuits': '',
                'gender': '',
                'gss_code': '',
                'homepage_url': '',
                'honorific_prefix': '',
                'honorific_suffix': '',
                'id': '2009',
                'image_copyright': '',
                'image_uploading_user': '',
                'image_uploading_user_notes': '',
                'image_url': '',
                'linkedin_url': '',
                'mapit_url': '',
                'name': 'Tessa Jowell',
                'old_person_ids': '',
                'parlparse_id': '',
                'party_ec_id': 'PP53',
                'party_id': 'party:53',
                'party_lists_in_use': 'False',
                'party_list_position': '',
                'party_name': 'Labour Party',
                'party_ppc_page_url': '',
                'post_id': '65808',
                'post_label': 'Dulwich and West Norwood',
                'proxy_image_url_template': '',
                'theyworkforyou_url': '',
                'twitter_username': '',
                'twitter_user_id': '',
                'wikipedia_url': '',
            }
        )

    def test_constituency_with_winner(self):
        response = self.app.get('/election/2015/post/14419/edinburgh-east')
        response.mustcontain('<div class="candidates__elected">')
        response.mustcontain('<div class="candidates__known">')

        response.mustcontain(no='Unset the current winners')

    def test_constituency_with_winner_record_results_user(self):
        response = self.app.get(
            '/election/2015/post/14419/edinburgh-east',
            user=self.user_who_can_record_results
        )
        response.mustcontain('Unset the current winners')

    def test_constituency_with_may_be_standing(self):
        response = self.app.get('/election/2015/post/14419/edinburgh-east')
        response.mustcontain('if these candidates from earlier elections are standing')
        response.mustcontain(no='These candidates from earlier elections are known not to be standing again')

    def test_constituency_with_not_standing(self):
        response = self.app.get('/election/2015/post/65808/dulwich-and-west-norwood')
        response.mustcontain('These candidates from earlier elections are known not to be standing again')
        response.mustcontain(no='if these candidates from earlier elections are standing')

    def test_mark_not_standing_no_candidate(self):
        response = self.app.get(
            '/election/2015/post/14419/edinburgh-east',
            user=self.user,
        )

        csrftoken = self.app.cookies['csrftoken']
        response = self.app.post(
            '/election/2015/candidacy/delete',
            {
                'person_id': '9999',
                'post_id': '14419',
                'source': 'test data',
                'csrfmiddlewaretoken': csrftoken,
            },
            expect_errors=True,
        )

        self.assertEqual(response.status_code, 404)

    def test_mark_not_standing_no_post(self):
        response = self.app.get(
            '/election/2015/post/14419/edinburgh-east',
            user=self.user,
        )

        csrftoken = self.app.cookies['csrftoken']
        response = self.app.post(
            '/election/2015/candidacy/delete',
            {
                'person_id': '181',
                'post_id': '9999',
                'source': 'test data',
                'csrfmiddlewaretoken': csrftoken,
            },
            expect_errors=True,
        )

        self.assertEqual(response.status_code, 404)

    def test_mark_standing_no_candidate(self):
        response = self.app.get(
            '/election/2015/post/14419/edinburgh-east',
            user=self.user,
        )

        csrftoken = self.app.cookies['csrftoken']
        response = self.app.post(
            '/election/2015/candidacy',
            {
                'person_id': '9999',
                'post_id': '14419',
                'source': 'test data',
                'csrfmiddlewaretoken': csrftoken,
            },
            expect_errors=True,
        )

        self.assertEqual(response.status_code, 404)

    def test_mark_standing_no_post(self):
        response = self.app.get(
            '/election/2015/post/14419/edinburgh-east',
            user=self.user,
        )

        csrftoken = self.app.cookies['csrftoken']
        response = self.app.post(
            '/election/2015/candidacy',
            {
                'person_id': '5163',
                'post_id': '9999',
                'source': 'test data',
                'csrfmiddlewaretoken': csrftoken,
            },
            expect_errors=True,
        )

        self.assertEqual(response.status_code, 404)

    def test_mark_candidate_not_standing(self):
        response = self.app.get(
            '/election/2015/post/14419/edinburgh-east',
            user=self.user,
        )

        csrftoken = self.app.cookies['csrftoken']
        response = self.app.post(
            '/election/2015/candidacy/delete',
            {
                'person_id': '818',
                'post_id': '14419',
                'source': 'test data',
                'csrfmiddlewaretoken': csrftoken,
            },
            expect_errors=True,
        )

        membership = MembershipExtra.objects.filter(
            base__person_id=818,
            base__post__extra__slug='14419',
            post_election__election__slug='2015'
        )
        self.assertFalse(membership.exists())

        person_extra = PersonExtra.objects.get(
            base__id=818
        )
        not_standing = person_extra.not_standing.all()
        self.assertTrue(self.election in not_standing)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.location,
            "/election/2015/post/14419/edinburgh-east"
        )

    def test_mark_may_stand_actually_standing(self):
        response = self.app.get(
            '/election/2015/post/14419/edinburgh-east',
            user=self.user,
        )

        csrftoken = self.app.cookies['csrftoken']
        response = self.app.post(
            '/election/2015/candidacy',
            {
                'person_id': '5163',
                'post_id': '14419',
                'source': 'test data',
                'csrfmiddlewaretoken': csrftoken,
            },
            expect_errors=True,
        )

        membership = MembershipExtra.objects.filter(
            base__person_id=5163,
            base__post__extra__slug='14419',
            post_election__election__slug='2015'
        )

        self.assertTrue(membership.exists())

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.location,
            "/election/2015/post/14419/edinburgh-east"
        )

    def test_mark_may_stand_not_standing_again(self):
        response = self.app.get(
            '/election/2015/post/14419/edinburgh-east',
            user=self.user,
        )

        csrftoken = self.app.cookies['csrftoken']
        response = self.app.post(
            '/election/2015/candidacy/delete',
            {
                'person_id': '5163',
                'post_id': '14419',
                'source': 'test data',
                'csrfmiddlewaretoken': csrftoken,
            },
            expect_errors=True,
        )

        membership = MembershipExtra.objects.filter(
            base__person_id=5163,
            base__post__extra__slug='14419',
            post_election__election__slug='2015'
        )
        self.assertFalse(membership.exists())

        person_extra = PersonExtra.objects.get(
            base__id=5163
        )
        not_standing = person_extra.not_standing.all()
        self.assertTrue(self.election in not_standing)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.location,
            "/election/2015/post/14419/edinburgh-east"
        )

    def test_mark_not_standing_standing_again(self):
        response = self.app.get(
            '/election/2015/post/65808/dulwich-and-west-norwood',
            user=self.user,
        )

        csrftoken = self.app.cookies['csrftoken']
        response = self.app.post(
            '/election/2015/candidacy',
            {
                'person_id': '4322',
                'post_id': '65808',
                'source': 'test data',
                'csrfmiddlewaretoken': csrftoken,
            },
            expect_errors=True,
        )

        membership = MembershipExtra.objects.filter(
            base__person_id=4322,
            base__post__extra__slug='65808',
            post_election__election__slug='2015'
        )

        self.assertTrue(membership.exists())

        person_extra = PersonExtra.objects.get(
            base__id=4322
        )
        not_standing = person_extra.not_standing.all()
        self.assertFalse(self.election in not_standing)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.location,
            "/election/2015/post/65808/dulwich-and-west-norwood"
        )

    def test_return_404_when_post_not_associated_with_election(self):
        # Now that post is not associated with the 2015 election, so
        # viewing a page with election: 2015 and post: DIW:E05005004
        # should return a 404.
        response = self.app.get(
            '/election/2015/post/DIW:E05005004/whatever',
            expect_errors=True,
        )
        self.assertEqual(response.status_code, 404)
