import tempfile
import pypandoc

from django.core.files.base import ContentFile
from raven.contrib.django.raven_compat.models import client

ACCEPTED_FILE_TYPES = ["docx", "pdf"]


class PandocConversionError(Exception):
    pass


def convert_sopn_to_pdf(uploaded_file):
    """
    Takes a File-like object, attempts to convert it to a PDF, and returns the
    new file that can then be used to store against an OfficialDocument
    """
    filetype = uploaded_file.name.split(".")[-1].lower()
    if filetype not in ACCEPTED_FILE_TYPES:
        raise PandocConversionError(f"Cannot convert {filetype} files")

    if filetype == "pdf":
        return uploaded_file

    print(
        f"Warning! This file type is not supported; trying to convert {uploaded_file.name} to pdf"
    )

    with tempfile.NamedTemporaryFile(suffix=".pdf") as temp_file:
        # convert the html and save to a temp file
        try:
            pypandoc.convert_text(
                uploaded_file.read(),
                to="pdf",
                format=filetype,
                outputfile=temp_file.name,
            )
        except RuntimeError:
            client.captureException()
            raise PandocConversionError()

        # return with converted file object and updated name
        pdf_file_name = uploaded_file.name.replace(f".{filetype}", ".pdf")
        return ContentFile(content=temp_file.file.read(), name=pdf_file_name)
