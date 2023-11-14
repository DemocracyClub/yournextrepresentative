import os
from io import StringIO
from time import sleep

import boto3
from django.core.management.base import BaseCommand
from official_documents.models import OfficialDocument, TextractResult
from sopn_parsing.models import AWSTextractParsedSOPN

# # this is a single page pdf SoPN for testing
# test_sopn = (
#     "ynr/apps/sopn_parsing/management/commands/test_sopns/HackneySOPN.pdf"
# )

# # this is a multipage page html saved as pdf SoPN for testing
test_sopn = "ynr/apps/sopn_parsing/management/commands/test_sopns/BurySOPN.pdf"

accepted_file_types = [
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".tif",
    ".tiff",
]


s3 = boto3.client("s3")
textract_client = boto3.client("textract")
session = boto3.session.Session(
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.environ.get("AWS_SECURITY_TOKEN"),
)
official_document = OfficialDocument.objects.get(id=1)


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.start_detection(test_sopn)

    def start_detection(self, test_sopn):
        """This is Step 1 of the SOPN parsing process using AWS Textract.
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/textract/client/get_document_analysis.html#
        """

        with open(test_sopn, "rb") as file:
            file_bytes = bytearray(file.read())
        region = "eu-west-2"
        bucket_name = "public-sopns"
        s3_client = boto3.client("s3", region_name=region)
        object_key = "test/test_sopn.pdf"

        response = s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=file_bytes,
        )
        print(f"Uploaded bytes to s3://{bucket_name}/{object_key}")
        response = textract_client.start_document_analysis(
            DocumentLocation={
                "S3Object": {
                    "Bucket": bucket_name,
                    "Name": object_key,
                }
            },
            FeatureTypes=["TABLES", "FORMS"],
            OutputConfig={
                "S3Bucket": "public-sopns",
                "S3Prefix": "test",
            },
        )
        if response["JobId"]:
            job_id = response["JobId"]
            self.get_job_results(job_id)
        else:
            print("Job failed to start")
            raise Exception("Job failed to start")

    def get_job_results(self, job_id):
        """This is Step 2 of the SOPN parsing process using AWS Textract.
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/textract/client/get_document_analysis.html#
        """
        textract_result = textract_client.get_document_analysis(JobId=job_id)
        while textract_result["JobStatus"] not in ["SUCCEEDED", "FAILED"]:
            sleep(5)
            textract_result = textract_client.get_document_analysis(
                JobId=job_id
            )

        if textract_result["JobStatus"] == "SUCCEEDED":
            TextractResult.objects.update_or_create(
                official_document=official_document,
                defaults={"job_id": job_id, "json_response": textract_result},
            )
            print(f"Job succeeded:{job_id}")
            print(
                "The number of pages in this document is:",
                textract_result["DocumentMetadata"]["Pages"],
            )
            self.transform_response_into_df(textract_result)
        elif textract_result["JobStatus"] == "FAILED":
            print(f"Job failed:{job_id}")
            print(textract_result["StatusMessage"])
        else:
            print(f"Job {job_id} still running")

    def map_blocks(self, blocks, block_type):
        return {
            block["Id"]: block
            for block in blocks
            if block["BlockType"] == block_type
        }

    def get_children_ids(self, block):
        for rels in block.get("Relationships", []):
            if rels["Type"] == "CHILD":
                yield from rels["Ids"]

    def transform_response_into_df(self, textract_result):
        """This step is to transform the raw data into a pandas dataframe so
        that we can then weave it into the existing parsing process.
        before we try to match parties."""
        # with credit to https://maxhalford.github.io/blog/textract-table-to-pandas/
        # keep an eye on this as it may be useful: https://pypi.org/project/amazon-textract-response-parser/
        # for now, we're just going to use the raw data
        import pandas as pd

        blocks = textract_result["Blocks"]
        tables = self.map_blocks(blocks, "TABLE")
        cells = self.map_blocks(blocks, "CELL")
        words = self.map_blocks(blocks, "WORD")
        selections = self.map_blocks(blocks, "SELECTION_ELEMENT")
        lines = self.map_blocks(blocks, "LINE")

        dataframes = []

        if tables:
            # if there are tables, we know this is a structured document
            for table in tables.values():
                # Determine all the cells that belong to this table
                table_cells = [
                    cells[cell_id] for cell_id in self.get_children_ids(table)
                ]

                # Determine the table's number of rows and columns
                n_rows = max(cell["RowIndex"] for cell in table_cells)
                n_cols = max(cell["ColumnIndex"] for cell in table_cells)
                content = [[None for _ in range(n_cols)] for _ in range(n_rows)]

                # Fill in each cell
                for cell in table_cells:
                    cell_contents = [
                        words[child_id]["Text"]
                        if child_id in words
                        else selections[child_id]["SelectionStatus"]
                        for child_id in self.get_children_ids(cell)
                    ]
                    i = cell["RowIndex"] - 1
                    j = cell["ColumnIndex"] - 1
                    content[i][j] = " ".join(cell_contents)

                dataframe = pd.DataFrame(content[1:], columns=content[0])
                dataframes.append(dataframe)
        elif lines:
            print(
                "No tables found. This may be an html SoPN. Let's try to parse the lines."
            )
            sopn_string_list = []
            for block in blocks:
                if block["BlockType"] == "LINE":
                    sopn_string_list.append(block["Text"].replace("\n", ","))
            sopn_string = " ".join(sopn_string_list)
            string_io = StringIO(sopn_string)
            dataframe = pd.read_csv(string_io)
        else:
            pass
        AWSTextractParsedSOPN.objects.create(
            sopn=official_document,
            raw_data=dataframe.to_json(),
            raw_data_type="pandas",
            parsed_data=dataframe.to_json(),
            status="parsed",
        )
