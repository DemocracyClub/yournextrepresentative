"""
CSV fields are defined as a mapping of the CSV column name and
a Django ORM database expression.

The idea is that each field knows how to fetch itself from the database, and
all fetching is done in the SQL query at the database end.

This allows the resulting query to be returned to Django without the need to
iterate over each row and perform any sort of action on it.

Fields marked as `core` will _always_ be included in the CSV output.

All other fields are optional.

"""

from collections import OrderedDict
from dataclasses import dataclass
from typing import Callable, Dict, Literal, Optional, Union

from django.core.files.storage import default_storage
from django.db.models import BooleanField, CharField, Expression
from django.db.models.expressions import Case, Combinable, F, Value, When
from django.db.models.functions import Concat, Substr
from django.template.defaultfilters import truncatechars
from django.urls import reverse
from django.utils.safestring import SafeString
from ynr_refactoring.settings import PersonIdentifierFields


@dataclass
class CSVField:
    value: Union[str, Expression, Combinable]
    type: Literal["attr", "expr"]
    value_group: Literal["person", "candidacy", "election", "results"]
    label: str
    core: bool = False
    formatter: Optional[Callable] = None
    value_type: str = "str"


def link_formatter(value, url):
    return SafeString(f"""<a href="{url}">{value}</a>""")


csv_fields: Dict[str, CSVField] = OrderedDict()
csv_fields["person_id"] = CSVField(
    value="person_id",
    type="attr",
    value_group="person",
    core=True,
    formatter=lambda value: link_formatter(
        value, reverse("person-view", kwargs={"person_id": value})
    ),
    label="Person ID",
)
csv_fields["person_name"] = CSVField(
    value="person_name",
    type="attr",
    core=True,
    value_group="person",
    label="Person name",
)

csv_fields["election_id"] = CSVField(
    value=F("ballot_paper__election__slug"),
    type="expr",
    core=True,
    value_group="election",
    formatter=lambda value: link_formatter(
        value, reverse("election_view", kwargs={"election": value})
    ),
    label="Election ID",
)

csv_fields["ballot_paper_id"] = CSVField(
    value="ballot_paper",
    type="attr",
    core=True,
    value_group="election",
    formatter=lambda value: link_formatter(
        value, reverse("election_view", kwargs={"election": value})
    ),
    label="Ballot paper ID",
)

csv_fields["election_date"] = CSVField(
    value="election_date",
    type="attr",
    core=True,
    value_group="election",
    label="Election date",
)
csv_fields["election_current"] = CSVField(
    value=F("ballot_paper__election__current"),
    type="expr",
    core=True,
    value_group="election",
    label="Current election (boolean)",
)
csv_fields["by_election"] = CSVField(
    value=Case(
        When(ballot_paper__ballot_paper_id__contains=".by.", then=Value(True)),
        default=Value(False),
        output_field=BooleanField(),
    ),
    type="expr",
    value_group="election",
    label="By-election (boolean)",
)
csv_fields["party_name"] = CSVField(
    value="party_name",
    type="attr",
    core=True,
    value_group="candidacy",
    label="Party name",
)
csv_fields["party_description_text"] = CSVField(
    value=F("membership__party_description_text"),
    type="expr",
    value_group="candidacy",
    label="Party description",
)
csv_fields["legacy_party_id"] = CSVField(
    value=F("party__legacy_slug"),
    type="expr",
    value_group="candidacy",
    label="Legacy party ID (not recommended)",
)
csv_fields["party_id"] = CSVField(
    value="party_id",
    type="attr",
    core=True,
    value_group="candidacy",
    label="Party ID",
)
csv_fields["party_list_position"] = CSVField(
    value="party_list_position",
    type="attr",
    value_group="candidacy",
    label="Party list position",
)
csv_fields["party_lists_in_use"] = CSVField(
    value=F("ballot_paper__election__party_lists_in_use"),
    type="expr",
    value_group="candidacy",
    label="Party lists in use (boolean)",
)
csv_fields["gss"] = CSVField(
    value=Case(
        When(
            ballot_paper__post__identifier__startswith="gss:",
            then=Substr(F("ballot_paper__post__identifier"), 5),
        ),
        default_value="",
    ),
    type="expr",
    value_group="election",
    label="GSS code (if availible)",
)
csv_fields["post_id"] = CSVField(
    type="expr",
    value=F(
        "ballot_paper__post__identifier",
    ),
    value_group="election",
    label="Post ID",
)
csv_fields["post_label"] = CSVField(
    type="expr",
    value=F("ballot_paper__post__label"),
    core=True,
    value_group="election",
    label="Post label",
)
csv_fields["cancelled_poll"] = CSVField(
    type="expr",
    value=F("ballot_paper__cancelled"),
    core=True,
    value_group="election",
    label="Cancelled poll (boolean)",
)
csv_fields["nuts1"] = CSVField(
    type="expr",
    value=F("ballot_paper__tags__NUTS1__value"),
    value_group="election",
    label="NUTS1 name",
)
csv_fields["seats_contested"] = CSVField(
    type="expr",
    value=F("ballot_paper__winner_count"),
    core=True,
    value_group="election",
    label="Seats contested",
)
csv_fields["organisation_name"] = CSVField(
    type="expr",
    value=F("ballot_paper__post__organization__name"),
    value_group="election",
    label="Organisation name",
)
csv_fields["previous_party_affiliations"] = CSVField(
    type="expr",
    value=F("membership__previous_party_affiliations"),
    value_group="candidacy",
    label="Previous party affiliations (Welsh candidacies only)",
)

csv_fields["votes_cast"] = CSVField(
    type="expr",
    value=F("membership__result__num_ballots"),
    value_group="results",
    label="Votes cast",
    value_type="int",
)

csv_fields["elected"] = CSVField(
    type="attr",
    value="elected",
    value_group="results",
    label="Elected",
)

csv_fields["tied_vote_winner"] = CSVField(
    type="expr",
    value=F("membership__result__tied_vote_winner"),
    value_group="results",
    label="Tied vote winner (Boolean)",
)
csv_fields["rank"] = CSVField(
    type="expr",
    value=F("membership__result__rank"),
    value_group="results",
    label="Rank",
)
csv_fields["turnout_reported"] = CSVField(
    type="expr",
    value=F("ballot_paper__resultset__num_turnout_reported"),
    value_group="results",
    label="Reported turnout",
)
csv_fields["spoilt_ballots"] = CSVField(
    type="expr",
    value=F("ballot_paper__resultset__num_spoilt_ballots"),
    value_group="results",
    label="Reported spoilt ballots",
)
csv_fields["total_electorate"] = CSVField(
    type="expr",
    value=F("ballot_paper__resultset__total_electorate"),
    value_group="results",
    label="Electorate",
)
csv_fields["turnout_percentage"] = CSVField(
    type="expr",
    value=F("ballot_paper__resultset__turnout_percentage"),
    value_group="results",
    label="Turnout %",
)
csv_fields["results_source"] = CSVField(
    type="expr",
    value=F("ballot_paper__resultset__source"),
    value_group="results",
    label="Results source",
)

for identifier in PersonIdentifierFields:
    csv_fields[identifier.name] = CSVField(
        type="expr",
        value=F(f"identifiers__{identifier.name}"),
        value_group="person",
        label=identifier.value,
    )

csv_fields["gender"] = CSVField(
    type="expr",
    value=F("person__gender"),
    value_group="person",
    label="Gender",
)

csv_fields["birth_date"] = CSVField(
    type="expr",
    value=F("person__birth_date"),
    value_group="person",
    label="Year of birth",
)

csv_fields["favourite_biscuit"] = CSVField(
    type="expr",
    value=F("person__favourite_biscuit"),
    value_group="person",
    label="Favourite Biscuit",
)
csv_fields["statement_to_voters"] = CSVField(
    type="expr",
    value=F("person__biography"),
    value_group="person",
    label="Statement to voters",
    formatter=lambda value: truncatechars(value, 100),
)

storages_url = default_storage.url("")

csv_fields["image"] = CSVField(
    type="expr",
    value=Case(
        When(
            person__image__image__isnull=False,
            then=Concat(
                Value(storages_url),
                F("person__image__image"),
                output_field=CharField(),
            ),
        ),
        default=Value(None),
        output_field=CharField(),
    ),
    value_group="person",
    label="Image URL",
)


def get_core_fieldnames():
    return [name for name, field in csv_fields.items() if field.core]
