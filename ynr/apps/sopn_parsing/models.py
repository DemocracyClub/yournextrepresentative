import json
import re
from io import BytesIO

import pandas
from django.core.files.images import ImageFile
from django.db import models
from django.utils.functional import cached_property
from model_utils.models import TimeStampedModel
from textractor.parsers import response_parser
from textractor.parsers.response_parser import parse


class CamelotParsedSOPN(TimeStampedModel):
    """
    A model for storing the parsed data out of a PDF
    where data has been extracted using Camelot.

    """

    official_document = models.OneToOneField(
        "official_documents.OfficialDocument",
        on_delete=models.CASCADE,
        null=True,
    )
    sopn = models.OneToOneField(
        "official_documents.BallotSOPN", on_delete=models.CASCADE, null=True
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


def AWSTextractParsedSOPNImage_upload_path(instance, filename):
    return f"AWSTextractParsedSOPNImages/{instance.pk}/{filename}"


class AWSTextractParsedSOPNImage(models.Model):
    image = models.ImageField(upload_to=AWSTextractParsedSOPNImage_upload_path)
    parsed_sopn = models.ForeignKey(
        "AWSTextractParsedSOPN", on_delete=models.CASCADE, related_name="images"
    )

    @staticmethod
    def pil_to_content_image(pil_image, filename):
        """
        Takes a PIL image and returns an ImageFile
        """
        image_io = BytesIO()
        pil_image.save(image_io, format="PNG")
        return ImageFile(image_io, name=filename)


class AWSTextractParsedSOPN(TimeStampedModel):
    """
    A model for storing the parsed data out of a PDF
    where data has been extracted using AWS Textract.

    """

    official_document = models.OneToOneField(
        "official_documents.OfficialDocument",
        on_delete=models.CASCADE,
        null=True,
    )
    sopn = models.OneToOneField(
        "official_documents.BallotSOPN", on_delete=models.CASCADE, null=True
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

    @cached_property
    def as_pandas(self):
        if not self.parsed_data:
            return None
        import pandas

        pandas.set_option("display.max_colwidth", None)
        # df = pandas.DataFrame.from_dict(json.loads(self.parsed_data))
        return self.parse_raw_data()

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

        last_title = None
        force_process_table = False
        found_situation_of_poll = False

        for page in parsed.pages:
            for layout in page.layouts[:5]:
                if "polling station" in layout.text.lower():
                    found_situation_of_poll = True
                    break
            if found_situation_of_poll:
                break

            for i, initial_table in enumerate(page.tables):
                if initial_table.column_count < 3:
                    force_process_table = True
                    continue
                try:
                    table_title = initial_table.title.text
                except AttributeError:
                    table_title = ""
                if "polling station" in table_title.lower():
                    continue

                table = initial_table
                if not force_process_table or page.page_num == 1:
                    df = self.remove_non_table_header_content(
                        initial_table.to_pandas()
                    )
                else:
                    df = initial_table.to_pandas()
                # else:
                #     try:
                #         table = initial_table.strip_headers()
                #         df = table.to_pandas()
                #     except IndexError:
                #         df = self.remove_non_header_rows(initial_table.to_pandas())
                #
                if i > 0 or page.page_num > 1:
                    if not force_process_table:
                        df = self.remove_header_rows(df)
                    force_process_table = False

                if df.empty:
                    continue

                frames.append(df)

                current_title = getattr(table.title, "text", None)
                if last_title and current_title != last_title:
                    break
                last_title = current_title

        all_rows = []
        max_len = 0
        for df in frames:
            if df.empty:
                continue
            rows = df.values.tolist()
            all_rows.extend(rows)
            max_len = max(max_len, max(len(row) for row in rows))
        padded_rows = [row + [""] * (max_len - len(row)) for row in all_rows]
        df = pandas.DataFrame(padded_rows)
        # Don't parse situation of polling stations
        df.reset_index(drop=True, inplace=True)

        polling_station_index = df[
            df.apply(
                lambda row: row.astype(str)
                .str.contains("polling station", case=False)
                .any(),
                axis=1,
            )
        ].index
        if not polling_station_index.empty:
            polling_station_index = polling_station_index[0]
            if isinstance(polling_station_index, str):
                polling_station_index = int(polling_station_index)
            new_df = df.loc[: polling_station_index - 1]
            df = new_df

        self.parsed_data = df.to_json()
        return df

    def remove_non_table_header_content(self, df):
        """
        Some tables include rows that aren't headers. Remove them

        """
        # How many rows to scan form the top of a df
        max_search = 4

        for i in range(min(len(df), max_search)):
            if self.is_header_row(df.iloc[i]):
                return df.iloc[i:].copy()
        return df

    def remove_header_rows(self, df: pandas.DataFrame):
        """
        Given a data frame, remove header rows

        """
        # How many rows to scan form the top of a df
        max_search = 4
        header_start_index = 0
        header_row_found = False

        for i in range(min(len(df), max_search)):
            if self.is_header_row(df.iloc[i]):
                header_row_found = True
                break
            header_start_index += 1
        if header_row_found:
            df = df.iloc[header_start_index + 1 :].copy()
        return df

    def as_textractor_document(self):
        if not self.raw_data:
            return None
        return response_parser.parse(json.loads(self.raw_data))

    def normalise_row(self, row):
        """Convert a row to a cleaned, comparable list of strings."""
        return [
            str(re.sub("[^a-z\s]", "", cell.lower())).strip()
            for cell in row
            if cell
        ]

    def is_header_row(self, row):
        keywords = ["name", "first", "surname"]
        cleaned = self.normalise_row(row)
        if len(cleaned) <= 3:
            return False
        return any(any(kw in cell for kw in keywords) for cell in cleaned)

    def get_withdrawal_column(self):
        column_names = [
            "no longer",
            "withdrawal",
            "invalid",
            "decision",
        ]
        if self.as_pandas.empty:
            return None
        for i, heading in enumerate(self.as_pandas.iloc[0]):
            if any(col in str(heading) for col in column_names):
                return self.as_pandas[i]
        return None

    def withdrawal_rows(self):
        column_values = self.get_withdrawal_column()
        if column_values is None:
            return None
        # column_values = self.as_pandas[column].tolist()
        cells_with_value = []
        for i, row in enumerate(column_values):
            # Skip the header, as that always contains a value
            if i == 0:
                continue
            if row:
                cells_with_value.append(i)
        return cells_with_value

    def get_withdrawals_bboxes(self):
        return "{}"
        # headers = self.as_pandas.iloc[0].tolist()
        # get colmun index from headers
        column = "4"
        column_values = self.as_pandas[column].tolist()
        cells_with_value = []
        for i, row in enumerate(column_values):
            if row:
                cells_with_value.append(i)
        cells_with_value.pop(0)
        # Deal with more than one page
        textract_cells = []
        for table in self.as_textractor_document().tables:
            for cell in table.table_cells:
                # if str(cell.col_index-1) != column:
                #     continue
                if cell.row_index - 1 in cells_with_value:
                    textract_cells.append(cell)
        print(textract_cells)

        doc_height = 1429
        doc_width = 1010

        page = 1
        box_data = {page: []}
        for cell in textract_cells:
            absolute_x = cell.x * doc_width
            absolute_y = cell.y * doc_height
            absolute_width = cell.width * doc_width
            absolute_height = cell.height * doc_height
            box_data[page].append(
                {
                    "x": absolute_x,
                    "y": absolute_y,
                    "width": absolute_width,
                    "height": absolute_height,
                    "color": "red",
                    "lineWidth": 2,
                },
            )
        return json.dumps(box_data)
