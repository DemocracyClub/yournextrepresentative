from moderation_queue.models import QueuedImage


def normalise_queued_image(queued_image_id):
    qi = QueuedImage.objects.get(pk=queued_image_id)
    qi.normalise_image()
