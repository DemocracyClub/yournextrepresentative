import re


def shorten_post_label(post_label):
    return re.sub(r"^Member of Parliament for ", "", post_label)
