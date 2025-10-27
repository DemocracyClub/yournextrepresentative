from pathlib import Path

import pytest
from django.test import TestCase
from django.utils.safestring import SafeString
from frontend.templatetags.markdown_filter import (
    markdown_filter,
    markdown_it_filter,
)


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


allowed_markdown_input = """\
Bla bla bla

- unordered
- bullet
- list

**bold** _italic_

1. ordered
2. bullet
3. list
"""

allowed_markdown_expected = """\
<p>Bla bla bla</p>
<ul>
<li>unordered</li>
<li>bullet</li>
<li>list</li>
</ul>
<p><strong>bold</strong> <em>italic</em></p>
<ol>
<li>ordered</li>
<li>bullet</li>
<li>list</li>
</ol>
"""


class TestMarkdownItFilter(TestCase):
    def test_xss(self):
        self.assertHTMLEqual(
            markdown_it_filter('<script>alert("xss")</script>'),
            "<p>&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;</p>\n",
        )

    def test_allowed_markdown(self):
        """
        Assert that the markdown styles we do want to support i.e:
        - lists
        - bold, italic
        - blockquote
        render as HTML
        """
        self.assertHTMLEqual(
            markdown_it_filter(allowed_markdown_input),
            allowed_markdown_expected,
        )

    def test_forbidden_markdown(self):
        """
        Assert that the markdown styles we don't want to support
        i.e: most of the markdown spec
        does not get rendered to HTML
        """
        test_cases = [
            "blockquote",
            "code",
            "headings",
            "horizontal_rules",
            "html",
            "images",
            "links",
            "strikethrough",
            "tables",
        ]
        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                input_ = Path(
                    f"ynr/apps/frontend/tests/forbidden_markdown/input/{test_case}.txt"
                ).read_text()
                expected = Path(
                    f"ynr/apps/frontend/tests/forbidden_markdown/expected/{test_case}.txt"
                ).read_text()
                self.assertHTMLEqual(markdown_it_filter(input_), expected)
