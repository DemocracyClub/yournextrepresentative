from uk_results.management.commands.import_2017_parl_results import (
    Command as ResultsImporterCommand,
)


class Command(ResultsImporterCommand):
    """
    Imports results for the 2015 general election. The data was taken from the
    House of Commons website, and then published in the Democracy Club google
    drive to make it easier to import.
    Structure of the CSV is the same as the CSV for 2017 so no need to update
    the management command methods. Check the `import_2017_parl_results` to see
    how the data is imported.
    """

    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQyhBHD7jcAYTZbzguFb_As4UjbkY42vXNzonqFzmQbUWGc6L3upoAb4FTrxBPHeNWg-gBkCrJURpZQ/pub?gid=0&single=true&output=csv"
    election_date = "2015-05-07"
