import re

from sopn_parsing.helpers.text_helpers import clean_text
from parties.models import Party, PartyDescription
from bulk_adding.models import RawPeople

NAME_FIELDS = (
    "name of candidate",
    "names of candidate",
    "candidate name",
    "surname",
    "candidates surname",
    "other name",
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


def guess_name_field(row):
    for cell in row:
        if cell in NAME_FIELDS:
            return cell
    raise ValueError("No name guess for {}".format(row))


def guess_description_field(row):
    description_strings = ("description of candidate", "description")

    for cell in row:
        if cell in description_strings:
            return cell
    raise ValueError("No description guess for {}".format(row))


def clean_name(name):
    name = name.replace("\n", "")
    return re.sub(r"([A-Z\-]+)\s([A-Za-z\-\s]+)", "\g<2> \g<1>", name).title()


def clean_description(description):
    description = str(description)
    description = description.replace("\\n", "")
    description = description.replace("\n", "")
    description = re.sub("\s+", " ", description)
    return description


def get_description(description, sopn):
    description = clean_description(description)

    if not description:
        return None
    if description in INDEPENDENT_VALUES:
        return None

    try:
        description_model = PartyDescription.objects.get(
            description=description
        )
    except PartyDescription.DoesNotExist:
        try:
            description_model = PartyDescription.objects.filter(
                description__startswith=description,
                party__register=sopn.sopn.post_election.post.party_set.slug,
            ).first()
        except PartyDescription.DoesNotExist:
            return None
    return description_model


def get_party(description_model, description, sopn):
    if description_model:
        return description_model.party

    party_name = clean_description(description)
    qs = Party.objects.register(sopn.sopn.post_election.post.party_set.slug)
    if not party_name:
        return Party.objects.get(ec_id="ynmp-party:2")

    try:
        party_obj = qs.get(name=party_name)
    except Party.DoesNotExist:
        party_obj = None

    if not party_obj:
        raise ValueError("Unknown party")
    return party_obj


def parse_table(sopn, data):
    data.columns = clean_row(data.columns)
    try:
        name_field = guess_name_field(data.columns)
    except ValueError:
        return None
    try:
        description_field = guess_description_field(data.columns)
    except ValueError:
        return None

    ballot_data = []
    for row in iter_rows(data):
        name = clean_name(row[name_field])
        description = get_description(row[description_field], sopn)
        party = get_party(description, row[description_field], sopn)
        data = {"name": name, "party_id": party.ec_id}
        if description:
            data["description_id"] = description.pk
        ballot_data.append(data)
    return ballot_data


def parse_raw_data_for_ballot(ballot):
    """

    :type ballot: candidates.models.PostExtraElection
    """

    if ballot.candidates_locked:
        raise ValueError("Can't parse a locked ballot")

    if ballot.suggestedpostlock_set.exists():
        raise ValueError("Can't parse a ballot with lock suggestions")

    parsed_sopn_model = ballot.sopn.parsedsopn
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
        RawPeople.objects.update_or_create(
            ballot=parsed_sopn_model.sopn.post_election,
            defaults={
                "data": ballot_data,
                "source": "Parsed from {}".format(
                    parsed_sopn_model.sopn.source_url
                ),
                "source_type": RawPeople.SOURCE_PARSED_PDF,
            },
        )
        parsed_sopn_model.status = "parsed"
        parsed_sopn_model.save()
