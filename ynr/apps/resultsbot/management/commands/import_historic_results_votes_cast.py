from candidates.models import Ballot, LoggedAction
from candidates.models.db import ActionType, EditType
from popolo.models import Membership
from resultsbot.importers.base_historic_results_importer import (
    BaseImportHistoricResults,
)
from uk_results.models import CandidateResult, ResultSet


class Command(BaseImportHistoricResults):
    help = """
    Import historic results data from the resultsbot csv file
    """
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTHlLmw-K_n7kifq0V9biNOefUXG6ejAeMXp1t04R7y-8OnOvhji32gFL5Viu7KLruoSCJkO_ApdJRH/pub?gid=325499441&single=true&output=csv"

    def parse_csv(self, csv_file):
        ballot_to_updates = {}
        ballot_didnt_exist = []

        for row in csv_file:
            ballot_paper_id = row["ballot_paper_id"]
            person_id = row["person_id"]
            num_ballots = int(row["votes_cast"])
            source = row["results_source"]

            try:
                ballot = Ballot.objects.get(ballot_paper_id=ballot_paper_id)
                membership = ballot.membership_set.get(person_id=person_id)
                # Skip all voting systems that are not FPTP
                if ballot.nice_voting_system != "First Past The Post":
                    continue

                membership_update = (membership, num_ballots, source)

                if ballot_to_updates.get(ballot) is None:
                    ballot_to_updates[ballot] = [membership_update]
                else:
                    ballot_to_updates[ballot].append(membership_update)
            except Ballot.DoesNotExist:
                ballot_didnt_exist.append(ballot)
                continue
            except Membership.DoesNotExist:
                print(
                    f"Membership for person ID {person_id} in ballot paper ID {ballot_paper_id} does not exist. Please check manually"
                )
                continue

        for ballot in ballot_didnt_exist:
            print(
                f"Ballot paper ID {ballot.ballot_paper_id} does not exist in the database. Please check manually"
            )

        records_to_save = []

        for ballot, membership_updates in ballot_to_updates.items():
            if hasattr(ballot, "resultset"):
                result_set = ballot.resultset
                changed = False
                for membership, num_ballots, source in membership_updates:
                    if hasattr(membership, "result"):
                        if membership.result.num_ballots == num_ballots:
                            continue
                        membership.result.num_ballots = num_ballots
                        records_to_save.append(membership.result)
                        changed = True
                    else:
                        result = CandidateResult(
                            membership=membership,
                            result_set=ballot.resultset,
                            num_ballots=num_ballots,
                        )
                        records_to_save.append(result)
                        changed = True
                # If we updated any CandidateResults, we need to record the old version of the ResultSet
                # update its source and add it to the records to save
                if changed:
                    result_set.record_version(save=False)
                    csv_source = membership_updates[0][2]
                    result_set.source = f"{result_set.source} and {csv_source}"
                    records_to_save.append(result_set)
            else:
                # Only create a new ResultSet if we have num_ballots for all memberships
                if ballot.membership_set.count() != len(membership_updates):
                    continue
                # Use the source from the first membership update
                source = membership_updates[0][2]
                result_set = ResultSet(
                    ballot=ballot,
                    user=self.user,
                    source=source,
                )
                # Append the new result set so it is saved first, before the CandidateResults
                records_to_save.append(result_set)
                # Then instantiate a Candidate Result for each membership/num_ballots pair
                for membership, num_ballots, source in membership_updates:
                    result = CandidateResult(
                        result_set=result_set,
                        membership=membership,
                        num_ballots=num_ballots,
                    )
                    records_to_save.append(result)

        print(f"{len(records_to_save)} records to update.")

        return records_to_save

    def create_meta_events(self, record):
        # If we're saving a ResultSet, we need to create a LoggedAction
        if isinstance(record, ResultSet):
            ballot = record.ballot
            LoggedAction.objects.create(
                user=self.user,
                action_type=ActionType.ENTERED_RESULTS_DATA,
                source=record.source,
                ballot=ballot,
                edit_type=EditType.BOT.name,
            )
