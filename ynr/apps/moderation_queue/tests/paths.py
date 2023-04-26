from os.path import abspath, dirname, join

EXAMPLE_IMAGE_FILENAME = abspath(join(dirname(__file__), "example-image.jpg"))
BROKEN_IMAGE_FILENAME = abspath(
    join(dirname(__file__), "broke-image-example.htm")
)

ROTATED_IMAGE_FILENAME = abspath(
    join(dirname(__file__), "rotated_photo_with_exif.jpg")
)

QUEUED_IMAGE_FILENAME = abspath(
    join(dirname(__file__), "media/queued-images/example-queued-image.png")
)
