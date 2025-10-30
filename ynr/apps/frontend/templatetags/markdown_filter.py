import markdown
import nh3
from django import template
from django.utils.safestring import mark_safe
from markdown_it import MarkdownIt

register = template.Library()


"""
Note:
We are using two different markdown rendering libraries in this module
This is for historic reasons rather than because we strictly need to

See
https://github.com/DemocracyClub/WhoCanIVoteFor/pull/2299#:~:text=Other%20places%20we%20use%20markdown
"""


@register.filter(name="markdown")
def markdown_filter(text):
    cleaned_text = nh3.clean(text, tags={"a"})
    return mark_safe(markdown.markdown(cleaned_text, extensions=["nl2br"]))


markdown_filter.is_safe = True


@register.filter(name="markdown_subset")
def markdown_it_filter(text):
    """
    note using js-default preset here gives us XSS protection
    https://markdown-it-py.readthedocs.io/en/latest/security.html
    so we don't need to run the text through nh3
    """
    options = {
        "breaks": True  # nl2br
    }
    renderer = MarkdownIt("js-default", options).disable(
        [
            "table",
            "code",
            "fence",
            "blockquote",
            "backticks",
            "hr",
            "reference",
            "html_block",
            "heading",
            "lheading",
            "linkify",
            "strikethrough",
            "link",
            "image",
            "autolink",
            "html_inline",
        ]
    )
    html = renderer.render(text)
    return mark_safe(html)


markdown_it_filter.is_safe = True
