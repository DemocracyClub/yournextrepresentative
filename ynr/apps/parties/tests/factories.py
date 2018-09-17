import factory


class PartyFactory(factory.DjangoModelFactory):
    class Meta:
        model = "parties.Party"

    ec_id = factory.Sequence(lambda n: "PP{}".format(n))
    name = factory.Sequence(lambda n: "Party %d" % n)
    date_registered = "2001-01-01"
    legacy_slug = factory.Sequence(lambda n: "party:%d" % n)
    register = "GB"


class PartyDescriptionFactory(factory.DjangoModelFactory):
    class Meta:
        model = "parties.PartyDescription"


class PartyEmblemFactory(factory.DjangoModelFactory):
    class Meta:
        model = "parties.PartyEmblem"

    image = factory.django.ImageField()
    ec_emblem_id = factory.Sequence(lambda n: n)
