import json
import re
from os.path import join

from bulk_adding.models import RawPeople
from django.core.files.base import ContentFile
from django.core.files.storage import DefaultStorage
from parties.models import Party, PartyDescription
from sopn_parsing.helpers.text_helpers import clean_text
from nameparser import HumanName

from sopn_parsing.models import ParsedSOPN

FIRST_NAME_FIELDS = ["other name", "other names", "candidate forename"]
LAST_NAME_FIELDS = [
    "surname",
    "candidate surname",
    "candidates surname",
    "last name",
]
NAME_FIELDS = (
    FIRST_NAME_FIELDS
    + LAST_NAME_FIELDS
    + ["name of candidate", "names of candidate", "candidate name"]
)


INDEPENDENT_VALUES = ("Independent", "")


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
    if len(merge_row_cells(row)) >= avg_row:
        if contains_header_like_strings(row):
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
    description_strings = ("description of candidate", "description")

    for cell in row:
        if cell in description_strings:
            return cell
    raise ValueError("No description guess for {}".format(row))


def clean_name(name):
    """
    - Strips some special characters from the name string
    - Splits the string in to a list, removing any empty strings
    - Build a string to represent the last name by looking for all words that are in all caps
    - Build a string to represent the other names by looking for all words not in all caps
    - Strip whitespace in case last_names is empty and return string titleized
    """

    name = name.replace("\n", "")
    name = name.replace("`", "'")
    names = list(filter(None, name.split(" ")))
    last_names = clean_last_names(names)
    first_names = " ".join([name for name in names if not name.isupper()])
    full_name = f"{first_names} {last_names}".strip()
    return full_name


## Handles Mc and Mac and other mixed titlecase names
def clean_last_names(names):
    last_names = " ".join([name for name in names if name.isupper()])
    last_names = HumanName(last_names)
    last_names.capitalize()
    return str(last_names)


def clean_description(description):
    description = str(description)
    description = description.replace("\\n", "")
    description = description.replace("\n", "")
    description = description.replace("`", "'")
    description = re.sub(r"\s+", " ", description)
    return description


def get_description(description, sopn):
    description = clean_description(description)

    if not description:
        return None
    if description in INDEPENDENT_VALUES:
        return None

    register = sopn.sopn.ballot.post.party_set.slug.upper()

    # First try to get Party object with an exact match between parsed
    # description and the Party name
    # If we find one, return None, so that the pain Party object
    # is parsed in get_party below, and this will then be preselected
    # for the user on the form.
    party = Party.objects.register(register).current().filter(name=description)
    if party.exists():
        return None

    try:
        return PartyDescription.objects.get(
            description=description, party__register=register
        )
    except PartyDescription.DoesNotExist:
        pass

    # try to find any that start with parsed description
    qs = PartyDescription.objects.filter(
        description__istartswith=description, party__register=register
    )
    if qs.exists():
        return qs.first()

    # final check - if this is a Welsh version of a description, it will be at
    # the end of the description
    return PartyDescription.objects.filter(
        description__endswith=f"| {description}", party__register=register
    ).first()


def get_party(description_model, description, sopn):
    if description_model:
        return description_model.party

    party_name = clean_description(description)
    register = sopn.sopn.ballot.post.party_set.slug.upper()
    qs = Party.objects.register(register).current()
    if not party_name or party_name in INDEPENDENT_VALUES:
        return Party.objects.get(ec_id="ynmp-party:2")

    try:
        party_obj = qs.get(name=party_name)
    except Party.DoesNotExist:
        party_obj = None

    if not party_obj:
        raise ValueError("Unknown party")
    return party_obj


def get_name(row, name_fields):
    """
    Takes a list of name fields and returns a string of the values of each of
    the name fields in the row
    """
    return " ".join([row[field] for field in name_fields])


def parse_table(sopn, data):

    data.columns = clean_row(data.columns)
    try:
        name_fields = get_name_fields(data.columns)
    except ValueError:
        return None

    # if we have more than one name field try to order them
    if len(name_fields) > 1:
        name_fields = order_name_fields(name_fields)

    try:
        description_field = guess_description_field(data.columns)
    except ValueError:
        return None

    ballot_data = []
    for row in iter_rows(data):
        name = get_name(row, name_fields)
        if not name:
            continue
        name = clean_name(name)
        description = get_description(row[description_field], sopn)
        party = get_party(description, row[description_field], sopn)
        data = {"name": name, "party_id": party.ec_id}
        if description:
            data["description_id"] = description.pk
        ballot_data.append(data)
    return ballot_data


def parse_raw_data_for_ballot(ballot):
    """

    :type ballot: candidates.models.Ballot
    """
    if ballot.candidates_locked:
        raise ValueError("Can't parse a locked ballot")

    if ballot.suggestedpostlock_set.exists():
        raise ValueError("Can't parse a ballot with lock suggestions")

    try:
        parsed_sopn_model = ballot.sopn.parsedsopn
    except ParsedSOPN.DoesNotExist:
        raise ValueError("No Parsed SOPN")

    data = parsed_sopn_model.as_pandas
    cell_counts = [len(merge_row_cells(c)) for c in iter_rows(data)]

    header_found = False
    avg_row = sum(cell_counts) / float(len(cell_counts))
    for i, row in enumerate(iter_rows(data)):
        if not header_found:
            if looks_like_header(row, avg_row):
                data.columns = row
                data = data.drop(data.index[i])
                header_found = True
            else:
                try:
                    data = data.drop(data.index[i])
                except IndexError:
                    break
    if not header_found:
        # Don't try to parse if we don't think we know the header
        return None
    # We're now in a position where we think we have the table we want
    # with the columns set and other header rows removed.
    # Time to parse it in to names and parties
    try:
        ballot_data = parse_table(parsed_sopn_model, data)
    except ValueError:
        # Something went wrong. This will happen a lot. let's move on
        return None

    if ballot_data:
        # Check there isn't a rawpeople object from another (better) source
        rawpeople_qs = RawPeople.objects.filter(
            ballot=parsed_sopn_model.sopn.ballot
        ).exclude(source_type=RawPeople.SOURCE_PARSED_PDF)
        if not rawpeople_qs.exists():
            RawPeople.objects.update_or_create(
                ballot=parsed_sopn_model.sopn.ballot,
                defaults={
                    "data": ballot_data,
                    "source": "Parsed from {}".format(
                        parsed_sopn_model.sopn.source_url
                    ),
                    "source_type": RawPeople.SOURCE_PARSED_PDF,
                },
            )
        # We've done the parsing, so let's still save the result
        storage = DefaultStorage()
        desired_storage_path = join(
            "raw_people",
            "{}.json".format(parsed_sopn_model.sopn.ballot.ballot_paper_id),
        )
        storage.save(
            desired_storage_path,
            ContentFile(json.dumps(ballot_data, indent=4).encode("utf8")),
        )

        parsed_sopn_model.status = "parsed"
        parsed_sopn_model.save()
