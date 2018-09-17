from os.path import abspath, join, dirname

EXAMPLE_IMAGE_FILENAME = abspath(join(dirname(__file__), "example-image.jpg"))
BROKEN_IMAGE_FILENAME = abspath(
    join(dirname(__file__), "broke-image-example.htm")
)
