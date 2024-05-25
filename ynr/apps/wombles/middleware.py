from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class CheckProfileDetailsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated and request.user.username.startswith(
            "@@"
        ):
            add_profile_url = reverse("wombles:add_profile_details")
            ignore_urls_for_rediret = [
                add_profile_url,
                reverse("wombles:logout"),
            ]

            if request.path not in ignore_urls_for_rediret:
                return redirect(add_profile_url)

        return None
