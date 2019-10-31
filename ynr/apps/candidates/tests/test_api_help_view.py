from django_webtest import WebTest

from . import factories


class TestApiHelpView(WebTest):
    def setUp(self):
        factories.ElectionFactory.create(
            slug="2015", name="2015 General Election"
        )

    def test_api_help(self):
        response = self.app.get("/help/api")
        self.assertEqual(response.status_code, 301)
