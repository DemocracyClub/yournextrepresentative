import json

from django.db import models
from model_utils.models import TimeStampedModel
from pandas import concat
from textractor.parsers.response_parser import parse


class CamelotParsedSOPN(TimeStampedModel):
    """
    A model for storing the parsed data out of a PDF
    where data has been extracted using Camelot.

    """

    sopn = models.OneToOneField(
        "official_documents.OfficialDocument", on_delete=models.CASCADE
    )
    raw_data = models.TextField()
    raw_data_type = models.CharField(max_length=255, default="pandas")
    parsed_data = models.TextField(null=True)
    status = models.CharField(max_length=255, default="unparsed")

    @property
    def as_pandas(self):
        import pandas

        pandas.set_option("display.max_colwidth", None)
        return pandas.DataFrame.from_dict(json.loads(self.raw_data))

    @property
    def data_as_html(self):
        if self.raw_data_type == "pandas":
            data = self.as_pandas
            header = data.iloc[0]
            data = data[1:]
            data.columns = header
            return data.to_html(index=False, escape=False).replace(
                "\\n", "<br>"
            )
        return None


class AWSTextractParsedSOPNStatus(models.TextChoices):
    NOT_STARTED = "NOT_STARTED", "Not Started"
    SUCCEEDED = "SUCCEEDED", "Succeeded"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    FAILED = "FAILED", "Failed"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS", "Partial Success"


class AWSTextractParsedSOPN(TimeStampedModel):
    """
    A model for storing the parsed data out of a PDF
    where data has been extracted using AWS Textract.

    """

    sopn = models.OneToOneField(
        "official_documents.OfficialDocument", on_delete=models.CASCADE
    )
    job_id = models.CharField(max_length=100)
    raw_data = models.TextField()
    raw_data_type = models.CharField(max_length=255, default="pandas")
    parsed_data = models.TextField(null=True)
    status = models.CharField(
        max_length=255,
        choices=AWSTextractParsedSOPNStatus.choices,
        default=AWSTextractParsedSOPNStatus.NOT_STARTED,
    )

    @property
    def as_pandas(self):
        import pandas

        pandas.set_option("display.max_colwidth", None)
        return pandas.DataFrame.from_dict(json.loads(self.parsed_data))

    def parse_raw_data(self):
        """
        Use AWS Textractor to convert the raw JSON response
        to a Pandas dataframe (and then to JSON for storing
        on the model).

        It's possible for Textract to detect more than one
        table per document. Default to merging them all
        into one table.
        :return:
        """
        # User Textractor to parse the raw JSON
        parsed = parse(json.loads(self.raw_data))
        # Store all data frames in a list
        frames = []

        # Table headers that we've seen
        for table in parsed.tables:
            # Get the pandas version of the table
            df = table.to_pandas()
            frames.append(df)

        # Merge all the dataframes
        df = concat(
            frames,
            ignore_index=True,
        )
        self.parsed_data = df.to_json()
