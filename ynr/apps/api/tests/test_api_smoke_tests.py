from django_webtest import WebTest

from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin


class TestAPI(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()

    def test_each_endpoint(self):
        endpoints_to_ignore = ["candidates_for_postcode"]
        for version in ("v0.9", "next"):
            response = self.app.get("/api/{}/".format(version))
            for name, url in response.json.items():
                # This slightly odd dance is needed because
                # pytest doesn't actually support subtests yet
                # (see https://github.com/pytest-dev/pytest/issues/1367)
                # Use try/except/failureException to log the endpoint that
                # failed. Unlike proper subtests, this will fail the test,
                # but hopefully writing it like this will mean it starts working
                # if/when pytest supports subtests properly
                if name in endpoints_to_ignore:
                    # Ignore some endpoints as they require more than a simple
                    # request and check for 200
                    continue
                with self.subTest(name, url=url):
                    response = self.app.get(url, expect_errors=True)
                    try:
                        self.assertEqual(response.status_code, 200)
                    except:
                        raise self.failureException(
                            "Error with '{}' {} endpoint".format(version, name)
                        )
