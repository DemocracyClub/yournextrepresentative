import factory


class QueuedImageFactory(factory.django.DjangoModelFactory):
    image = factory.django.ImageField()
    decision = "undecided"

    class Meta:
        model = "moderation_queue.QueuedImage"
