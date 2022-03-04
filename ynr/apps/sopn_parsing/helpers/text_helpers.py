import re
import unicodedata


def clean_text(text, recheck=True):
    """
    Simple interface for cleaning text in a generic way
    """
    text = _clean_text(text, recheck=True)
    return text


def clean_page_text(text):
    return _clean_text(text, split_braces=False)


def _clean_text(text, recheck=True, split_braces=True):
    """
    Internal interface for cleaning text
    """
    text = str(text)
    text = text.lower()
    text = text.replace("\xa0", " ")
    text = unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode()
    text = text.replace("'", "")
    text = text.replace("`", "")
    text = text.replace(" & ", " and ")
    text = text.replace(".", "")
    text = text.replace(",", "")
    text = text.replace("-y-", " y ")
    text = text.replace("\n", " ")
    text = text.replace("\\n", " ")
    text = re.sub(r"[\s]+", " ", text)
    text = re.sub(r"(^[a-z])\s([a-z][a-z]+)", r"\1\2", text)
    text = re.sub(r"(^[0-9])\s", r"", text)
    text = text.replace("*", "")
    text = " ".join(char for char in text.split() if not char.isdigit())
    if split_braces:
        text = text.split("(")[0].strip()
    if recheck:
        return _clean_text(text, recheck=False, split_braces=split_braces)
    return text.strip()


class NoTextInDocumentError(ValueError):
    pass


class MatchedPagesError(Exception):
    pass
