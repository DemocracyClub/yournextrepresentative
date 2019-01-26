from django.views.generic import DetailView
from django.contrib.auth.models import User


class SingleWombleView(DetailView):
    template_name = "wombles/single_womble.html"
    model = User
