from django_webtest import WebTest


class TestSignUpPage(WebTest):
    def test_invalid_email(self):
        response = self.app.get("/accounts/signup/")

        self.assertEqual(response.status_code, 200)
        # submit the form with an prohibited email domain
        form = response.forms["signup_form"]
        form["email"] = "john@me.gov"
        form["password1"] = "password"
        form["password2"] = "password"
        response = form.submit()
        self.assertFormError(
            response,
            "form",
            "email",
            "Please use a non-government or non-academic email address.",
        )
