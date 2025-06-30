from candidates.models import Ballot, LoggedAction
from candidates.models.db import ActionType, EditType
from candidates.views.version_data import get_change_metadata
from parties.models import Party
from resultsbot.importers.base_historic_results_importer import (
    BaseImportHistoricResults,
)


class Command(BaseImportHistoricResults):
    help = """
    Import historic results data from the resultsbot csv file
    """
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTHlLmw-K_n7kifq0V9biNOefUXG6ejAeMXp1t04R7y-8OnOvhji32gFL5Viu7KLruoSCJkO_ApdJRH/pub?gid=1004143866&single=true&output=csv"

    def parse_csv(self, csv_file):
        ballot_didnt_exist = []
        records_to_save = []

        for row in csv_file:
            ballot_paper_id = row["ballot_paper_id"]
            person_id = row["person_id"]
            party_ec_id = row["party_id"]
            try:
                ballot = Ballot.objects.get(ballot_paper_id=ballot_paper_id)
                membership = ballot.membership_set.get(person_id=person_id)
                if membership.party.ec_id != party_ec_id:
                    party = Party.objects.get(ec_id=party_ec_id)
                    membership.party = party
                    membership.party_name = party.name
                    # If the party has only one description, set it as the party_description
                    # Otherwise we can't be sure which one to use
                    if party.descriptions.count() == 1:
                        membership.party_description = (
                            party.descriptions.first()
                        )
                    membership.party_description_text = ""

                    records_to_save.append(membership)

            except Ballot.DoesNotExist:
                ballot_didnt_exist.append(ballot_paper_id)
                continue

        print(
            f"Found {len(records_to_save)} memberships to update party_id. Please check manually"
        )
        for ballot in ballot_didnt_exist:
            print(
                f"Ballot paper ID {ballot} does not exist in the database. Please check manually"
            )
        return records_to_save

    def create_meta_events(self, membership):
        change_metadata = get_change_metadata(None, self.source, user=self.user)
        person = membership.person
        person.record_version(change_metadata)
        person.save()

        LoggedAction.objects.create(
            user=self.user,
            action_type=ActionType.PERSON_UPDATE,
            popit_person_new_version=change_metadata["version_id"],
            person=person,
            source=self.source,
            edit_type=EditType.BOT.name,
        )
