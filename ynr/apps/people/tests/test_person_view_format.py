from candidates.tests.auth import TestUserMixin
from django.test import TestCase
from django_webtest import WebTest
from people.forms.forms import BasePersonForm


class PersonFormsTestCase(TestUserMixin, WebTest, TestCase):
    def test_clean_biography_returns(self):
        test_biography = "I am delighted to have been selected to be the Liberal Democrat candidate for the upcoming\r Trull, Pitminster and Corfe by-election. This\r comes after the resignation of Cllr Martin Hill for\r personal reasons; we’d like to thank Martin for\r his efforts.\r \r I am a member of Trull Parish Council and have\r enjoyed working with my colleagues there to\r achieve much on behalf of the village.\r I am well- known in Trull for my performances\r with Trull Players, my work with the Trull Party in\r the Park and for my walks through the fields and\r lanes with my rather noisy Labradoodle Poppy. I\r have lived in Staplehay since 1999 where my 3\r children attended local schools, scouts and clubs.\r Other voluntary work has been as Chair of the\r Trull Primary PTA, Social Secretary for Trull Tennis\r Club and Secretary for Trull Players.\r \r Local councillor Sarah Wakefield and I have\r known our existing for 20 years. We hold each\r other in great respect and believe working as a\r team we will serve this community well.\r \r I am thrilled to have this opportunity to represent you on the\r council. I have campaigned for this community\r on many local issues and have much experience\r in acting as a village representative through work\r on the developments at Comeytrowe and\r Broadlands, work on Canonsgrove and work on\r the Trull Neighbourhood Plan. I believe\r passionately in listening to the community and\r can be trusted to listen and act on your behalf."
        form = BasePersonForm(data={"biography": test_biography})
        cleaned_data = {}
        cleaned_data["biography"] = test_biography
        form.cleaned_data = cleaned_data
        cleaned_bio_text = "I am delighted to have been selected to be the Liberal Democrat candidate for the upcoming Trull, Pitminster and Corfe by-election. This comes after the resignation of Cllr Martin Hill for personal reasons; we’d like to thank Martin for his efforts.  I am a member of Trull Parish Council and have enjoyed working with my colleagues there to achieve much on behalf of the village. I am well- known in Trull for my performances with Trull Players, my work with the Trull Party in the Park and for my walks through the fields and lanes with my rather noisy Labradoodle Poppy. I have lived in Staplehay since 1999 where my 3 children attended local schools, scouts and clubs. Other voluntary work has been as Chair of the Trull Primary PTA, Social Secretary for Trull Tennis Club and Secretary for Trull Players.  Local councillor Sarah Wakefield and I have known our existing for 20 years. We hold each other in great respect and believe working as a team we will serve this community well.  I am thrilled to have this opportunity to represent you on the council. I have campaigned for this community on many local issues and have much experience in acting as a village representative through work on the developments at Comeytrowe and Broadlands, work on Canonsgrove and work on the Trull Neighbourhood Plan. I believe passionately in listening to the community and can be trusted to listen and act on your behalf."
        cleaned_bio = form.clean_biography()
        self.assertEqual(cleaned_bio, cleaned_bio_text)

    def test_clean_biography_many_newlines(self):
        test_biography = "paragraph with more than two newlines at the end\n\n\n\n\n\n\n\n\n\n\n\nFollowed by another paragraph with just two newlines.\n\nFollowed by a final paragraph."
        form = BasePersonForm(data={"biography": test_biography})
        cleaned_data = {}
        cleaned_data["biography"] = test_biography
        form.cleaned_data = cleaned_data
        cleaned_bio_text = "paragraph with more than two newlines at the end\n\nFollowed by another paragraph with just two newlines.\n\nFollowed by a final paragraph."
        cleaned_bio = form.clean_biography()
        self.assertEqual(cleaned_bio, cleaned_bio_text)
