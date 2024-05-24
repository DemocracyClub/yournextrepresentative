from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class CheckProfileDetailsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated and not request.user.username:
            add_profile_url = reverse("wombles:add_profile_details")

            if request.path != add_profile_url:
                return redirect(add_profile_url)

        return None
