import tempfile
import pypandoc

ACCEPTED_FILE_TYPES = ["docx", "html"]


def convert_sopn_to_pdf(uploaded_file):
    """
    Convert a SOPN to a PDF.
    """
    filetype = uploaded_file.name.split(".")[-1]
    if filetype == "pdf":
        return uploaded_file

    if uploaded_file.name.split(".")[-1] in ACCEPTED_FILE_TYPES:
        print(
            f"Warning! This file type is not supported; trying to convert {uploaded_file.name} to pdf"
        )

        with tempfile.NamedTemporaryFile(suffix=".pdf") as temp_file:
            # convert the html and save to a temp file
            pypandoc.convert_text(
                uploaded_file,
                to="pdf",
                format=filetype,
                outputfile=temp_file.name,
            )

            # save the pdf file to the uploaded file
            pdf_file_name = uploaded_file.name.replace(f".{filetype}", ".pdf")

            uploaded_file.save(name=pdf_file_name, content=temp_file, save=True)
    else:
        raise ValueError("File type is not supported")
    return uploaded_file
