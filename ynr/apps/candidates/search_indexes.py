from celery_haystack.indexes import CelerySearchIndex
from haystack import indexes

from people.models import Person


class PersonIndex(CelerySearchIndex, indexes.Indexable):
    # FIXME: this doesn't seem to work for partial names despite what
    # docs say
    text = indexes.EdgeNgramField(document=True, use_template=True)
    name = indexes.CharField(model_attr="name")
    family_name = indexes.CharField(model_attr="family_name")
    given_name = indexes.CharField(model_attr="given_name")
    additional_name = indexes.CharField(model_attr="additional_name")
    last_updated = indexes.DateTimeField(model_attr="updated_at")

    def get_updated_field(self):
        return "updated_at"

    def get_model(self):
        return Person
