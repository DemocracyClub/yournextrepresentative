from django.views.generic import DetailView
from people.models import Person


class PersonFacebookAdsView(DetailView):
    queryset = Person.objects.all().prefetch_related("facebookadvert_set")
    pk_url_kwarg = "person_id"
    template_name = "facebook_data/person_ads.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["total_max_spend"] = round(
            sum(
                [
                    float(x.get_spend_range[1])
                    for x in self.object.facebookadvert_set.all()
                ]
            )
        )

        return context
