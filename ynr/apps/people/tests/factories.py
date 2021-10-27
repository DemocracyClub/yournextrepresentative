import factory


class PersonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "people.Person"

    name = factory.Faker("name")
    versions = []


class PersonIdentifierFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "people.PersonIdentifier"

    person = factory.SubFactory(PersonFactory)
