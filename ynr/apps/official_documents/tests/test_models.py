"""
Basic smoke tests for OfficialDocument model
"""


from django.test import TestCase

from official_documents.models import OfficialDocument

from candidates.tests.factories import (
    ElectionFactory,
    ParliamentaryChamberFactory,
    PostFactory,
)

from compat import text_type


class TestModels(TestCase):
    def setUp(self):
        election = ElectionFactory.create(
            slug="parl.2015-05-07", name="2015 General Election"
        )
        commons = ParliamentaryChamberFactory.create()
        self.post = PostFactory.create(
            elections=(election,),
            organization=commons,
            slug="dulwich-and-west-norwood",
            label="Member of Parliament for Dulwich and West Norwood",
        )
        self.ballot = self.post.postextraelection_set.get()

    def test_unicode(self):
        doc = OfficialDocument(
            post_election=self.ballot, source_url="http://example.com/"
        )

        self.assertEqual(
            text_type(doc),
            "parl.dulwich-and-west-norwood.2015-05-07 (http://example.com/)",
        )
