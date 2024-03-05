import copy
import json
from io import StringIO
from time import sleep
from typing import Any, Optional, Tuple

import boto3
import pandas as pd
from botocore.client import Config
from django.conf import settings
from django.core.management import call_command
from django.db import IntegrityError
from official_documents.models import OfficialDocument
from pdfminer.pdftypes import PDFException
from sopn_parsing.helpers.pdf_helpers import SOPNDocument
from sopn_parsing.helpers.text_helpers import NoTextInDocumentError
from sopn_parsing.models import AWSTextractParsedSOPN


def extract_pages_for_ballot(ballot):
    """
    Try to extract the page numbers for the latest SOPN document related to this
    ballot.

    Because documents can apply to more than one ballot, we also perform
    "drive by" parsing of other ballots contained in a given document.

    :type ballot: candidates.models.Ballot

    """
    try:
        sopn = SOPNDocument(
            file=ballot.sopn.uploaded_file,
            source_url=ballot.sopn.source_url,
            election_date=ballot.election.election_date,
        )

        sopn.match_all_pages()
        if len(sopn.pages) == 1:
            call_command(
                "sopn_parsing_aws_textract",
                "--start-analysis",
                "--get-results",
                "--ballot",
                ballot.ballot_paper_id,
            )

    except NoTextInDocumentError:
        raise NoTextInDocumentError(
            f"Failed to extract pages for {ballot.sopn.uploaded_file.path} as a NoTextInDocumentError was raised"
        )
    except PDFException:
        print(
            f"{ballot.ballot_paper_id} failed to parse as a PDFSyntaxError was raised"
        )
        raise PDFException(
            f"Failed to extract pages for {ballot.sopn.uploaded_file.path} as a PDFSyntaxError was raised"
        )


config = Config(retries={"max_attempts": 5})

textract_client = boto3.client(
    "textract", region_name=settings.TEXTRACT_S3_BUCKET_REGION, config=config
)


class TextractSOPNHelper:
    """Get the AWS Textract results for a given SOPN."""

    def __init__(
        self,
        official_document: OfficialDocument,
        bucket_name: str = None,
    ):
        self.official_document = official_document

        self.bucket_name = bucket_name or settings.AWS_STORAGE_BUCKET_NAME

    def start_detection(self, replace=False) -> Optional[AWSTextractParsedSOPN]:
        parsed_sopn = getattr(
            self.official_document, "awstextractparsedsopn", None
        )
        if parsed_sopn and not replace:
            return None
        response = self.textract_start_document_analysis()
        try:
            textract_result, _ = AWSTextractParsedSOPN.objects.update_or_create(
                sopn=self.official_document,
                defaults={"raw_data": "", "job_id": response["JobId"]},
            )
            return textract_result
        except IntegrityError as e:
            raise IntegrityError(
                f"Failed to create AWSTextractParsedSOPN for {self.official_document.ballot.ballot_paper_id}: error {e}"
            )

    def textract_start_document_analysis(self):
        return textract_client.start_document_analysis(
            DocumentLocation={
                "S3Object": {
                    "Bucket": self.bucket_name,
                    "Name": f"{settings.MEDIA_URL}/{self.official_document.uploaded_file.name}".lstrip(
                        "/"
                    ),
                }
            },
            FeatureTypes=["TABLES", "FORMS"],
            OutputConfig={
                "S3Bucket": settings.TEXTRACT_S3_BUCKET_NAME,
                "S3Prefix": "raw_textract_responses",
            },
        )

    def textract_get_document_analysis(self, job_id, next_token=None):
        if next_token:
            return textract_client.get_document_analysis(
                JobId=job_id, NextToken=next_token
            )
        return textract_client.get_document_analysis(JobId=job_id)

    def update_job_status(self, blocking=False):
        COMPLETED_STATES = ("SUCCEEDED", "FAILED", "PARTIAL_SUCCESS")
        status = self.official_document.awstextractparsedsopn.status
        if status in COMPLETED_STATES:
            # TODO: should we delete the instance of the textract result?
            return None
        textract_result = self.official_document.awstextractparsedsopn
        job_id = textract_result.job_id

        response = self.textract_get_document_analysis(job_id)
        textract_result.status = response["JobStatus"]

        if blocking:
            while response["JobStatus"] not in [
                "SUCCEEDED",
                "FAILED",
                "PARTIAL_SUCCESS",
            ]:
                sleep(5)
                response = self.textract_get_document_analysis(job_id)

        if response["JobStatus"] == "SUCCEEDED":
            # It's possible that the returned result will be truncated.
            # In this case you need to use the next token to get
            # subsequent parts of the response.
            blocks = []
            while True:
                for block in response["Blocks"]:
                    blocks.append(block)
                if "NextToken" not in response:
                    break
                response = self.textract_get_document_analysis(
                    job_id, next_token=response["NextToken"]
                )
            response["Blocks"] = blocks

        textract_result.raw_data = json.dumps(response)
        textract_result.save()
        return textract_result


class TextractSOPNParsingHelper:
    """Helper class to extract the AWS Textract blocks for a given SOPN
    and return the results as a dataframe. This is not to be confused with
    the SOPN parsing functionality that matches fields including
    candidates to parties."""

    def __init__(self, official_document: OfficialDocument):
        self.official_document = official_document

    def get_rows_columns_map(self, table_result, blocks_map):
        # This method and the get_text method are adapted from the AWS Textract
        # https://docs.aws.amazon.com/textract/latest/dg/examples-export-table-csv.html
        # the first two rows are generally headers but this needs to be refactored to be
        # to be useful in the context of the SOPN parsing.
        rows = {}
        scores = []
        for relationship in table_result["Relationships"]:
            if relationship["Type"] == "CHILD":
                for child_id in relationship["Ids"]:
                    cell = blocks_map[child_id]
                    if cell["BlockType"] == "CELL":
                        row_index = cell["RowIndex"]
                        col_index = cell["ColumnIndex"]
                        if row_index not in rows:
                            # create new row
                            rows[row_index] = {}

                        # get confidence score
                        scores.append(str(cell["Confidence"]))
                        # get the text value
                        rows[row_index][col_index] = self.get_text(
                            cell, blocks_map
                        )

        return rows, scores

    def get_text(self, result, blocks_map):
        text = ""
        if "Relationships" in result:
            for relationship in result["Relationships"]:
                if relationship["Type"] == "CHILD":
                    for child_id in relationship["Ids"]:
                        word = blocks_map[child_id]
                        if word["BlockType"] == "WORD":
                            text += word["Text"] + " "
                        if (
                            word["BlockType"] == "SELECTION_ELEMENT"
                            and word["SelectionStatus"] == "SELECTED"
                        ):
                            text += "X "
        return text

    def create_df_from_textract_result(self):
        textract_result = self.official_document.awstextractparsedsopn
        response = textract_result.raw_data
        response = json.loads(response)
        blocks = response["Blocks"]
        blocks_map = {}
        table_blocks = []
        text = []
        for block in blocks:
            blocks_map[block["Id"]] = block
            if block["BlockType"] == "TABLE":
                table_blocks.append(block)
            if block["BlockType"] == "LINE" or block["BlockType"] == "WORD":
                text.append(block["Text"])

        df = {}
        # if there are tables, the text could be mapped with column headers into a csv
        # before saving in a dataframe which may improve the quality of the parsed data
        # later on.
        if len(table_blocks) > 0:
            for index, table in enumerate(table_blocks):
                df += self.prepare_df_from_table_results(
                    table, blocks_map, index + 1, self.official_document
                )
        # if there are no tables, we can extract the text as a list and save as a dataframe.
        elif len(text) > 0:
            df = pd.DataFrame(text)
            self.save_dataframe_to_aws_sopn(df, self.official_document)

        else:
            return "No data found"
        return df

    def prepare_df_from_table_results(
        self, table_result, blocks_map, table_index, official_document
    ):
        rows, scores = self.get_rows_columns_map(table_result, blocks_map)

        table_id = "Table_" + str(table_index)

        # get cells.
        csv = "Table: {0}".format(table_id)
        for row_index, cols in rows.items():
            for col_index, text in cols.items():
                csv += "{}".format(text)

        try:
            df = pd.read_csv(StringIO(csv))
            print(df.shape)
        except Exception as e:
            print(f"Error: {e}")
            df = pd.DataFrame()
        self.save_dataframe_to_aws_sopn(df, official_document)
        return df

    def save_dataframe_to_aws_sopn(self, df, official_document):
        aws_textract_parsed_sopn = (
            AWSTextractParsedSOPN.objects.update_or_create(
                sopn=official_document
            )
        )

        if aws_textract_parsed_sopn:
            aws_textract_parsed_sopn[0].raw_data = df.to_json()
            aws_textract_parsed_sopn[0].save()

        return aws_textract_parsed_sopn
