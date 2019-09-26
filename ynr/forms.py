from allauth.account.forms import LoginForm, SignupForm


class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["login"].label = "Username or email address"
        # Remove the placeholder text, which just adds noise:
        for field in ("login", "password"):
            del self.fields[field].widget.attrs["placeholder"]


class CustomSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ("username", "email", "password1", "password2"):
            del self.fields[field].widget.attrs["placeholder"]
