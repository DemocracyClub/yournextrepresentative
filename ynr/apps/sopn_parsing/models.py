import json

from django.db import models
from model_utils.models import TimeStampedModel


class ParsedSOPN(TimeStampedModel):
    """
    A model for storing the parsed data out of a PDF

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
