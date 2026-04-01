import os
from datetime import date

# This should be one of:
# ELECTION_STATS
# SOPN_TRACKER
# RESULTS_PROGRESS
# BY_ELECTIONS
FRONT_PAGE_CTA = "BY_ELECTIONS"

if os.environ.get("DC_ENVIRONMENT", "local") in ("local", "production"):
    FRONT_PAGE_CTA = "SOPN_TRACKER"
    SHOW_DATA_DOWNLOAD = False
    SOPN_TRACKER_INFO = {
        "election_date": "2026-05-07",
        "election_name": "2026 elections",
    }
    SOPN_SHEET_URL = "https://docs.google.com/spreadsheets/d/1ZpFy1dhmgLSpAhyLcSxsOnLzMH2znlyoS_lgFCjDkqg/edit?gid=0#gid=0"
    SOPN_DATES = [
        ("Scotland", date(year=2026, month=4, day=1)),
        ("England and Wales", date(year=2026, month=4, day=9)),
        # ("England and Wales", date(year=2024, month=4, day=5)),
        # ("Northern Ireland", date(year=2023, month=4, day=24)),
        # ("United Kingdom", date(year=2024, month=6, day=7)),
    ]

    DATA_DOWNLOAD_INFO = {
        "election_date": "2026-05-07",
        "election_name": "2026 local elections",
        "election_regex": "2026-05-07$",
    }

    SCHEDULED_ELECTION_DATES = ["2026-05-07"]

if os.environ.get("DC_ENVIRONMENT", "local") == "training":
    FRONT_PAGE_CTA = "SOPN_TRACKER"
    SOPN_TRACKER_INFO = {
        "election_name": "2026 local elections",
        # ynr/apps/elections/uk/management/commands/uk_create_training_elections.py
        "election_date": "2026-05-08",
    }
    SOPN_SHEET_URL = "#"
    SHOW_DATA_DOWNLOAD = False
