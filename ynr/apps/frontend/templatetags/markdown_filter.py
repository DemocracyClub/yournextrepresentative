import bleach
import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="markdown")
def markdown_filter(text):
    cleaned_text = bleach.clean(text)
    return mark_safe(markdown.markdown(cleaned_text, extensions=["nl2br"]))


markdown_filter.is_safe = True
