from candidates.models import Ballot, LoggedAction
from candidates.models.db import ActionType, EditType
from candidates.views.version_data import get_change_metadata
from results.models import ResultEvent
from resultsbot.importers.base_historic_results_importer import (
    BaseImportHistoricResults,
)


class Command(BaseImportHistoricResults):
    help = """
    Import historic results data from the resultsbot csv file
    """
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTHlLmw-K_n7kifq0V9biNOefUXG6ejAeMXp1t04R7y-8OnOvhji32gFL5Viu7KLruoSCJkO_ApdJRH/pub?gid=1257491027&single=true&output=csv"

    def parse_csv(self, csv_file):
        ballot_didnt_exist = []
        records_to_save = []

        for row in csv_file:
            ballot_paper_id = row["ballot_paper_id"]
            person_id = row["person_id"]
            elected = row["elected"].lower() == "t"
            try:
                ballot = Ballot.objects.get(ballot_paper_id=ballot_paper_id)
                membership = ballot.membership_set.get(person_id=person_id)

                if membership.elected != elected:
                    membership.elected = elected
                    records_to_save.append(membership)

            except Ballot.DoesNotExist:
                ballot_didnt_exist.append(ballot_paper_id)
                continue

        print(
            f"Found {len(records_to_save)} memberships to update elected status."
        )
        for ballot in ballot_didnt_exist:
            print(f"Ballot paper ID {ballot} does not exist in the database.")
        return records_to_save

    def create_meta_events(self, membership):
        ballot = membership.ballot

        if membership.elected:
            ResultEvent.objects.create(
                election=ballot.election,
                winner=membership.person,
                post=ballot.post,
                old_post_id=ballot.post.slug,
                old_post_name=ballot.post.label,
                winner_party=membership.party,
                source=self.source,
                user=self.user,
            )
            change_metadata = get_change_metadata(
                None, self.source, user=self.user
            )

            membership.person.record_version(change_metadata)
            membership.person.save()

            LoggedAction.objects.create(
                user=self.user,
                action_type=ActionType.SET_CANDIDATE_ELECTED,
                popit_person_new_version=change_metadata["version_id"],
                person=membership.person,
                source=self.source,
                edit_type=EditType.BOT.name,
            )
