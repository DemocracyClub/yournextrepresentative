import tempfile

import pypandoc
import sentry_sdk
from django.core.files.base import ContentFile


class PandocConversionError(Exception):
    pass


def convert_docx_to_pdf(uploaded_file: ContentFile):
    """
    Takes a File-like docx object, attempts to convert it to a PDF, and returns the
    new file.
    """
    with tempfile.NamedTemporaryFile(
        suffix=".docx"
    ) as in_file, tempfile.NamedTemporaryFile(suffix=".pdf") as out_file:
        # convert the docx and save to a temp file
        with open(in_file.name, "wb") as f:
            uploaded_file.seek(0)
            f.write(uploaded_file.read())
        try:
            pypandoc.convert_file(
                in_file.name,
                to="pdf",
                format="docx",
                outputfile=out_file.name,
            )
        except RuntimeError as e:
            sentry_sdk.capture_exception()
            raise PandocConversionError(e)

        # return with converted file object and updated name
        pdf_file_name = uploaded_file.name.replace(".docx", ".pdf")
        return ContentFile(content=out_file.file.read(), name=pdf_file_name)
