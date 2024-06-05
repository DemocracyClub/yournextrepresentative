from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.utils.http import url_has_allowed_host_and_scheme


class CheckProfileDetailsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated and request.user.username.startswith(
            "@@"
        ):
            next_url = request.GET.get("next")
            if not url_has_allowed_host_and_scheme(
                url=next_url, allowed_hosts={request.get_host()}
            ):
                next_url = None

            add_profile_url = reverse("wombles:add_profile_details")

            ignore_urls_for_rediret = [
                add_profile_url,
                reverse("wombles:logout"),
            ]
            if request.path not in ignore_urls_for_rediret:
                redirect_url = add_profile_url
                if next_url:
                    redirect_url = f"{add_profile_url}?next={next_url}"
                return redirect(redirect_url)

        return None
