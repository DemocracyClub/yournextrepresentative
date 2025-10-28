from datetime import date

# This should be one of:
# ELECTION_STATS
# SOPN_TRACKER
# RESULTS_PROGRESS
# BY_ELECTIONS
FRONT_PAGE_CTA = "BY_ELECTIONS"
SHOW_DATA_DOWNLOAD = False
SOPN_TRACKER_INFO = {
    "election_date": "2025-05-01",
    "election_name": "2025 local elections",
}
SOPN_SHEET_URL = "https://docs.google.com/spreadsheets/d/1SJQdgVe6N4PRoI70XR6XC02MIzchlyB2S3WKRR_GoBw/edit?gid=0#gid=0"
SOPN_DATES = [
    # ("Scotland", date(year=2023, month=3, day=30)),
    ("England", date(year=2025, month=5, day=1)),
    # ("England and Wales", date(year=2024, month=4, day=5)),
    # ("Northern Ireland", date(year=2023, month=4, day=24)),
    # ("United Kingdom", date(year=2024, month=6, day=7)),
]

DATA_DOWNLOAD_INFO = {
    "election_date": "2025-05-01",
    "election_name": "2025 local elections",
    "election_regex": "local.*.2025-05-01",
}

SCHEDULED_ELECTION_DATES = ["2025-05-01"]
