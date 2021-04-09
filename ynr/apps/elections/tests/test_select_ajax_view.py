from django.urls import reverse
from django_webtest import WebTest

from candidates.tests.uk_examples import UK2015ExamplesMixin


class TestPostsView(UK2015ExamplesMixin, WebTest):
    maxDiff = None

    def test_ajax_view_cache_headers(self):
        resp = self.app.get(reverse("ajax_ballots_for_select"))
        self.assertEqual(resp.headers["Cache-Control"], "max-age=60")

    def test_ajax_view(self):
        resp = self.app.get(reverse("ajax_ballots_for_select"))
        self.assertHTMLEqual(
            resp.text,
            """
            <option></option>
            <optgroup label='Maidstone local election'>
            <option value='local.maidstone.DIW:E05005004.2016-05-05' data-party-register='GB' data-uses-party-lists='False'>Shepway South Ward</option>
            </optgroup>
            <optgroup label='2015 General Election'>
            <option value='parl.65913.2015-05-07' data-party-register='GB' data-uses-party-lists='False'>Member of Parliament for Camberwell and Peckham</option>
            <option value='parl.65808.2015-05-07' data-party-register='GB' data-uses-party-lists='False'>Member of Parliament for Dulwich and West Norwood</option>
            <option value='parl.14419.2015-05-07' data-party-register='GB' data-uses-party-lists='False'>Member of Parliament for Edinburgh East</option>
            <option value='parl.14420.2015-05-07' data-party-register='GB' data-uses-party-lists='False'>Member of Parliament for Edinburgh North and Leith</option>
            </optgroup>""",
        )

    def test_locked_and_cancelled_ballots(self):
        self.maxDiff = None
        self.camberwell_post_ballot.cancelled = True
        self.camberwell_post_ballot.save()
        self.dulwich_post_ballot.candidates_locked = True
        self.dulwich_post_ballot.save()
        resp = self.app.get(reverse("ajax_ballots_for_select"))
        self.assertHTMLEqual(
            resp.text,
            """<option></option>
            <optgroup label='Maidstone local election'>
            <option value='local.maidstone.DIW:E05005004.2016-05-05' data-party-register='GB' data-uses-party-lists='False'>Shepway South Ward</option>
            </optgroup>
            <optgroup label='2015 General Election'>
            <option value='parl.65913.2015-05-07' data-party-register='GB' data-uses-party-lists='False'>Member of Parliament for Camberwell and Peckham (❌ cancelled)</option>
            <option data-party-register="GB" data-uses-party-lists="False" disabled="True" value="parl.65808.2015-05-07">Member of Parliament for Dulwich and West Norwood 🔐</option>
            <option value='parl.14419.2015-05-07' data-party-register='GB' data-uses-party-lists='False'>Member of Parliament for Edinburgh East</option>
            <option value='parl.14420.2015-05-07' data-party-register='GB' data-uses-party-lists='False'>Member of Parliament for Edinburgh North and Leith</option>
            </optgroup>""",
        )
