from django_webtest import WebTest


class TestVolunteerPage(WebTest):
    def test_volunteer_page(self):
        response = self.app.get("/volunteer/")

        self.assertEqual(200, response.status_code)
        self.assertContains(
            response,
            "Democracy needs you! How to Contribute: collect candidate information",
        )
