import re
import unicodedata


def clean_text(text, recheck=True):
    """
    Generally clean up text to make matching and searching easier.
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
    text = re.sub("[\s]+", " ", text)
    text = re.sub(r"(^[a-z])\s([a-z][a-z]+)", r"\1\2", text)
    text = re.sub(r"(^[0-9])\s", r"", text)
    text = text.replace("*", "")
    text = text.split("(")[0].strip()
    if recheck:
        return clean_text(text, recheck=False)
    return text.strip()


class NoTextInDocumentError(ValueError):
    pass
