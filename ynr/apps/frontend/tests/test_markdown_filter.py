import pytest
from django.utils.safestring import SafeString
from frontend.templatetags.markdown_filter import markdown_filter


@pytest.mark.parametrize(
    "input_text, expected_output",
    [
        # newline to linebreak
        (
            "This is a test.\nNew line.",
            "<p>This is a test.<br />\nNew line.</p>",
        ),
        # double newline to paragraph
        (
            "This is a test.\n\nNew paragraph.",
            "<p>This is a test.</p>\n<p>New paragraph.</p>",
        ),
        # list with newlines to list with linebreaks
        (
            """ 
    This is a list:
    - Item 1
    - Item 2
    - Item 3
    Text after a list.
    """,
            """<p>This is a list:<br />
    - Item 1<br />
    - Item 2<br />
    - Item 3<br />
    Text after a list.</p>""",
        ),
    ],
)
def test_markdown_filter(input_text, expected_output):
    result = markdown_filter(input_text)
    assert isinstance(result, SafeString)
    assert result == expected_output
