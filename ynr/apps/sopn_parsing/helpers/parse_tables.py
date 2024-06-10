import json
import re

from bulk_adding.models import RawPeople
from candidates.models import Ballot
from django.contrib.postgres.search import TrigramSimilarity
from django.core.files.base import ContentFile
from django.core.files.storage import DefaultStorage
from django.db.models import F, Value
from django.db.models.functions import Lower, Replace
from django.db.utils import DataError
from nameparser import HumanName
from pandas import DataFrame
from parties.models import Party, PartyDescription
from sopn_parsing.helpers.text_helpers import clean_text
from utils.db import Levenshtein

FIRST_NAME_FIELDS = [
    "other name",
    "other names",
    "candidate forename",
    "candidates other names",
    "other names in full",
    "other names / enwau eraill",
]
LAST_NAME_FIELDS = [
    "surname",
    "candidate surname",
    "candidates surname",
    "last name",
    "surname / cyfenw",
]
WELSH_NAME_FIELDS = [
    "enwr ymgeisydd",
    "enwr ymgeisydd candidate name",
    "enwr ymgeisydd name of candidate",
]
NAME_FIELDS = (
    FIRST_NAME_FIELDS
    + LAST_NAME_FIELDS
    + [
        "name of candidate",
        "names of candidate",
        "candidate name",
        "surname other names",
        "surname other names in full",
    ]
    + WELSH_NAME_FIELDS
)

INDEPENDENT_VALUES = ["independent", "", "annibynnol", "independents"]

WELSH_DESCRIPTION_VALUES = [
    "disgrifiad",
    "disgrifiad or ymgeisydd",
    "disgrifiad or ymgeisydd description of candidate",
]
DESCRIPTION_VALUES = [
    "description of candidate",
    "description",
] + WELSH_DESCRIPTION_VALUES


def iter_rows(data):
    counter = 0
    more = True
    while more:
        try:
            yield data.iloc[counter]
            counter += 1
        except IndexError:
            more = False


def merge_row_cells(row):
    return [c for c in row if c]


def clean_row(row):
    return [clean_text(c) for c in row]


def contains_header_like_strings(row):
    row_string = clean_text(row.to_string())
    if any(s in row_string for s in NAME_FIELDS):
        return True
    return False


def looks_like_header(row, avg_row):
    avg_row = avg_row - 3
    if len(merge_row_cells(row)) >= avg_row and contains_header_like_strings(
        row
    ):
        return True
    return False


def order_name_fields(name_fields):
    """
    Takes a list of name fields and attempts to find a field with in the
    LAST_NAME_FIELDS and move to the end of the list
    """
    for index, field in enumerate(name_fields):
        if field in LAST_NAME_FIELDS:
            # found the fieldname we think is for the last name,
            # so move that to the end of our name fields
            name_fields.append(name_fields.pop(index))
            break

    return name_fields


def get_name_fields(row):
    """
    Returns a list of name fields. This could be a single field or multiple
    fields.
    """
    name_fields = [cell for cell in row if cell in NAME_FIELDS]
    if not name_fields:
        raise ValueError("No name guess for {}".format(row))
    return name_fields


def guess_description_field(row):
    for cell in row:
        if cell in DESCRIPTION_VALUES:
            return cell
    raise ValueError("No description guess for {}".format(row))


def guess_previous_party_affiliations_field(data, sopn):
    data = clean_row(data)
    if not sopn.sopn.ballot.is_welsh_run:
        return None

    field_value = None

    for cell in data:
        if cell in ["statement of party membership"]:  # this could become more
            field_value = cell
            break

    return field_value


def clean_name(name):
    """
    - Strips some special characters from the name string
    - Splits the string in to a list, removing any empty strings
    - Build a string to represent the last name by looking for all words that are in all caps
    - Build a string to represent the other names by looking for all words not in all caps
    - Strip whitespace in case last_names is empty and return string titleized
    """
    name = name.replace("\n", " ")
    name = name.replace("`", "'")
    name = name.replace("\u2013", "\u002d")
    # remove multiple whitespaces
    name = " ".join(name.split())
    # this can leave extra whitespace after special chars so remove these
    name = name.replace("- ", "-")
    name = name.replace("' ", "'")

    if "commonly known as" in name:
        name = name.replace(")", "")
        name = name.split("commonly known as")[-1].replace(")", "").strip()

    names = list(filter(None, name.split(" ")))
    last_names = clean_last_names(names)
    first_names = " ".join([name for name in names if not name.isupper()])
    return f"{first_names} {last_names}".strip()


## Handles Mc and Mac and other mixed titlecase names
def clean_last_names(names):
    last_names = " ".join([name for name in names if name.isupper()])
    last_names = HumanName(last_names)
    last_names.capitalize()
    return str(last_names)


def clean_description(description):
    description = str(description)
    description = description.strip()
    description = description.replace("\\n", "")
    description = description.replace("\n", "")
    description = description.replace("`", "'")
    description = description.replace("&", "and")
    # change dash to hyphen to match how they are stored in our DB
    description = description.replace("\u2013", "\u002d")
    description = re.sub(r"\s+", " ", description)
    # handle edgecases for the green party to stop incorrectly matching against
    # Welsh descriptions
    if description.lower().strip() in [
        "the green party",
        "the green party candidate",
    ]:
        description = "Green Party"
    return description


def get_description(description, sopn):
    description = clean_description(description).strip()

    if not description:
        return None
    if description.lower() in INDEPENDENT_VALUES:
        return None

    description_value = Replace(
        Lower(Value(description)), Value("&"), Value("and")
    )
    register = sopn.sopn.ballot.post.party_set.slug.upper()

    # First try to get Party object with an exact match between parsed
    # description and the Party name

    # annotate search_text field to both QuerySets which normalizes name field
    # by changing '&' to 'and' this is then used instead of the name field for
    # string matching
    party_qs = (
        Party.objects.register(register)
        .current()
        .annotate(search_text=Lower(Replace("name", Value("&"), Value("and"))))
    )
    party = party_qs.filter(search_text=description_value)
    # If we find one, return None, so that the pain Party object
    # is parsed in get_party below, and this will then be preselected
    # for the user on the form.
    if party.exists():
        return None

    party_description_qs = PartyDescription.objects.annotate(
        search_text=Lower(Replace("description", Value("&"), Value("and")))
    )
    try:
        return party_description_qs.get(
            search_text=description_value, party__register=register
        )
    except (
        PartyDescription.DoesNotExist,
        PartyDescription.MultipleObjectsReturned,
    ) as e:
        print(e)
        pass

    # try to find any that start with parsed description
    description_obj = party_description_qs.filter(
        search_text__istartswith=description_value, party__register=register
    ).first()

    # Levenshtein
    try:
        qs = party_description_qs.annotate(
            lev_dist=Levenshtein(F("search_text"), description_value)
        ).order_by("lev_dist")
        description_obj = qs.filter(lev_dist__lte=3).first()
        if description_obj:
            print(
                f"{description} matched with {description_obj.description} with a distance of {description_obj.lev_dist}"
            )
            return description_obj
    except ValueError:
        print("Levenshtein failed")
        pass

    if description_obj:
        return description_obj

    # final check - if this is a Welsh version of a description, it will be at
    # the end of the description
    try:
        return party_description_qs.filter(
            search_text__endswith=f"| {description}", party__register=register
        ).first()
    except PartyDescription.DoesNotExist:
        print(f"Couldn't find description for {description}")
        pass


def get_party(description_model, description_str, sopn):
    if description_model:
        return description_model.party

    party_name = clean_description(description_str)
    register = sopn.sopn.ballot.post.party_set.slug.upper()

    # annotate search_text field which normalizes name field by changing '&' to 'and'
    # this is then used instead of the name field for string matching
    qs = (
        Party.objects.register(register)
        .active_for_date(date=sopn.sopn.ballot.election.election_date)
        .annotate(search_text=Replace("name", Value("&"), Value("and")))
    )
    if not party_name or party_name.lower().strip() in INDEPENDENT_VALUES:
        return Party.objects.get(ec_id="ynmp-party:2")

    try:
        return qs.get(search_text=party_name)
    except Party.DoesNotExist:
        party_obj = None

    qs = qs.annotate(
        lev_dist=Levenshtein("search_text", Value(party_name))
    ).order_by("lev_dist")
    party_obj = qs.filter(lev_dist__lte=5).first()
    if party_obj:
        print(
            f"{party_name} matched with {party_obj.name} with a distance of {party_obj.lev_dist}"
        )
        return party_obj

    # Last resort attempt - look for the most similar party object to help when
    # parsed name is missing a whitespace e.g. Barnsley IndependentGroup
    qs = qs.annotate(similarity=TrigramSimilarity("name", party_name)).order_by(
        "-similarity"
    )

    party_obj = qs.filter(similarity__gte=0.5).first()
    if not party_obj:
        closest = qs.first()
        print(f"Couldn't find party for {party_name}.")
        print(f"Closest is {closest.name} with similarity {closest.similarity}")

    return party_obj


def get_name(row, name_fields):
    """
    Takes a list of name fields and returns a string of the values of each of
    the name fields in the row
    """
    name = " ".join([row[field] for field in name_fields])
    return clean_name(name)


def add_previous_party_affiliations(party_str, raw_data, sopn):
    """
    Attempts to find previous party affiliations and add them to the data
    object. If no party can be found, returns the data unchanged.
    """
    if not party_str:
        return raw_data

    party = get_party(
        description_model=None, description_str=party_str, sopn=sopn
    )

    if not party:
        return raw_data

    raw_data["previous_party_affiliations"] = [party.ec_id]
    return raw_data


def parse_table(sopn, data):
    data.columns = clean_row(data.columns)

    name_fields = get_name_fields(data.columns)

    # if we have more than one name field try to order them
    if len(name_fields) > 1:
        name_fields = order_name_fields(name_fields)

    description_field = guess_description_field(data.columns)
    previous_party_affiliations_field = guess_previous_party_affiliations_field(
        data=data.columns, sopn=sopn
    )

    ballot_data = []
    for row in iter_rows(data):
        name = get_name(row, name_fields)
        # if we couldnt parse a candidate name skip this row
        if not name:
            continue

        description_obj = get_description(
            description=row[description_field], sopn=sopn
        )
        party_obj = get_party(
            description_model=description_obj,
            description_str=row[description_field],
            sopn=sopn,
        )
        if not party_obj:
            continue

        data = {"name": name, "party_id": party_obj.ec_id}
        if description_obj:
            data["description_id"] = description_obj.pk

        if previous_party_affiliations_field:
            data = add_previous_party_affiliations(
                party_str=row[previous_party_affiliations_field],
                raw_data=data,
                sopn=sopn,
            )

        ballot_data.append(data)
    return ballot_data


def parse_raw_data_for_ballot(ballot, reparse=False):
    """

    :type ballot: candidates.models.Ballot
    """
    if ballot.candidates_locked:
        raise ValueError(
            f"Can't parse a locked ballot {ballot.ballot_paper_id}"
        )

    if ballot.suggestedpostlock_set.exists():
        raise ValueError(
            f"Can't parse a ballot with lock suggestions {ballot.ballot_paper_id}"
        )
    # at this point, we may have two sets of data that need to both follow the same
    # parsing process. We need parse both but do we only save one to the RawPeople model?
    # or do we save both? If we save both, we need to make sure that the data is
    # consistent between the two sets of data. If we only save one, which one do we save?
    # do we save the one that has the most data? or do we save the one that has the most
    # data that matches the data in the RawPeople model? We should let the user choose
    # which one to save. In this case, we need to present the user with the two sets of
    # data and let them choose which one to save.
    parse_raw_data(ballot, reparse=reparse)


def parse_dataframe(ballot: Ballot, df: DataFrame):
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

    cell_counts = [len(merge_row_cells(c)) for c in iter_rows(df)]

    header_found = False
    avg_row = sum(cell_counts) / float(len(cell_counts) or 1)
    for row in iter_rows(df):
        if not header_found:
            if looks_like_header(row, avg_row):
                df.columns = row
                df = df.drop(row.name)
                header_found = True
            else:
                try:
                    df = df.drop(row.name)
                except IndexError:
                    break
    if not header_found:
        # Don't try to parse if we don't think we know the header
        print(f"We couldn't find a header for {ballot.ballot_paper_id}")
        return None
    # We're now in a position where we think we have the table we want
    # with the columns set and other header rows removed.
    # Time to parse it in to names and parties
    try:
        return parse_table(ballot, df)
    except ValueError as e:
        # Something went wrong. This will happen a lot. let's move on
        print(f"Error attempting to parse a table for {ballot.ballot_paper_id}")
        print(e.args[0])
        return None


def parse_raw_data(ballot: Ballot, reparse=False):
    """
    Given a Ballot, go and get the Camelot and the AWS Textract dataframes
    and process them
    """

    camelot_model = getattr(ballot.sopn, "camelotparsedsopn", None)
    camelot_data = {}
    textract_model = getattr(ballot.sopn, "awstextractparsedsopn", None)
    textract_data = {}
    if (
        camelot_model
        and camelot_model.raw_data_type == "pandas"
        and (reparse or not camelot_model.parsed_data)
    ):
        camelot_data = parse_dataframe(ballot, camelot_model.as_pandas)
    if (
        textract_model
        and textract_model.raw_data
        and textract_model.raw_data_type == "pandas"
        and (reparse or not textract_model.parsed_data)
    ):
        if not textract_model.parsed_data:
            textract_model.parse_raw_data()
        textract_data = parse_dataframe(ballot, textract_model.as_pandas)

    if camelot_data or textract_data:
        # Check there isn't a rawpeople object from another (better) source
        rawpeople_qs = RawPeople.objects.filter(ballot=ballot).exclude(
            source_type=RawPeople.SOURCE_PARSED_PDF
        )
        if not rawpeople_qs.exists():
            try:
                RawPeople.objects.update_or_create(
                    ballot=ballot,
                    defaults={
                        "data": camelot_data or "",
                        "textract_data": textract_data or "",
                        "source": "Parsed from {}".format(
                            ballot.sopn.source_url
                        ),
                        "source_type": RawPeople.SOURCE_PARSED_PDF,
                    },
                )
            except DataError:
                print(
                    f"DataError attempting to save RawPeople for {ballot.ballot_paper_id}"
                )
                return
        # We've done the parsing, so let's still save the result
        storage = DefaultStorage()
        storage.save(
            f"raw_people/camelot_{ballot.ballot_paper_id}.json",
            ContentFile(json.dumps(camelot_data, indent=4).encode("utf8")),
        )
        storage.save(
            f"raw_people/textract_{ballot.ballot_paper_id}.json",
            ContentFile(json.dumps(textract_data, indent=4).encode("utf8")),
        )
        if camelot_model:
            ballot.sopn.camelotparsedsopn.status = "parsed"
            ballot.sopn.camelotparsedsopn.save()
        if textract_model:
            ballot.sopn.awstextractparsedsopn.status = "parsed"
            ballot.sopn.awstextractparsedsopn.save()
