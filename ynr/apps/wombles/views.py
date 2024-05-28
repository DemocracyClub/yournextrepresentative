import hashlib

from candidates.models import LoggedAction
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import (
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)
from sesame.utils import get_query_string, get_user
from wombles.forms import LoginForm, UserProfileForm
from wombles.models import WombleTags


class MyProfile(LoginRequiredMixin, TemplateView):
    template_name = "wombles/my_profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        context["recent_edits"] = (
            LoggedAction.objects.filter(user=context["user"])
            .select_related("person", "ballot")
            .order_by("-created")[:50]
        )

        return context


class SingleWombleView(LoginRequiredMixin, DetailView):
    template_name = "wombles/single_womble.html"
    model = User

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["edits_over_time"] = (
            LoggedAction.objects.filter(user=self.object)
            .extra({"day": "date_trunc('week', date(created))"})
            .values("day")
            .annotate(edits=Count("pk"))
            .values("day", "edits")
            .order_by("day")
        )

        context[
            "edits_over_time"
        ] = self.object.womble_profile.edits_over_time()
        return context


class WombleTagsView(LoginRequiredMixin, ListView):
    model = WombleTags


class WombleTagView(LoginRequiredMixin, DetailView):
    slug_url_kwarg = "tag"
    slug_field = "label"

    def get_queryset(self):
        return WombleTags.objects.all().prefetch_related(
            "wombleprofile_set__user",
            "wombleprofile_set__tags",
            "wombleprofile_set__user__loggedaction_set",
        )


class LoginView(FormView):
    form_class = LoginForm
    template_name = "wombles/login.html"

    def make_fake_username(self, email):
        hash_object = hashlib.sha256(email.encode())
        # Convert the hash object to a hexadecimal string
        hashed_email = hash_object.hexdigest()
        # Optionally, you can shorten the hash for the username (e.g., first 10 characters)
        return f"@@{hashed_email[:10]}"

    def form_valid(self, form):
        """
        Create or retrieve a user trigger the send login email
        """
        user, created = User.objects.get_or_create(
            email=form.cleaned_data["email"],
        )
        if created:
            user.username = self.make_fake_username(form.cleaned_data["email"])
            user.set_unusable_password()
            user.save()

        self.send_login_url(user=user)
        messages.success(
            self.request,
            "Thank you, please check your email for your magic link to log in to your account.",
            fail_silently=True,
        )
        return HttpResponseRedirect(self.get_success_url())

    def send_login_url(self, user):
        """
        Send an email to the user with a link to authenticate and log in
        """
        querystring = get_query_string(user=user)
        domain = self.request.get_host()
        path = reverse("wombles:authenticate")
        url = f"{self.request.scheme}://{domain}{path}{querystring}"
        subject = (
            "Your magic link to log in to the Democracy Club Candidates site"
        )
        txt = render_to_string(
            template_name="wombles/email/login_message.txt",
            context={
                "authenticate_url": url,
                "subject": subject,
            },
        )
        return user.email_user(subject=subject, message=txt)

    def get_success_url(self):
        """
        Redirect to same page where success message will be displayed
        """
        return reverse("wombles:login")


class AuthenticateView(TemplateView):
    template_name = "wombles/authenticate.html"

    def get(self, request, *args, **kwargs):
        """
        Attempts to get user from the request, log them in, and redirect them to
        their profile page. Renders an error message if django-sesame fails to
        get a user from the request.
        """
        user = get_user(request)
        if not user:
            return super().get(request, *args, **kwargs)

        login(request, user)
        if not user.username:
            return redirect("wombles:add_profile_details")
        return redirect("/")


class UpdateProfileDetailsView(UpdateView):
    form_class = UserProfileForm
    template_name = "wombles/update_profile.html"

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse("wombles:my_profile")
