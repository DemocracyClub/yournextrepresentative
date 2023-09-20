from uk_election_timetables.calendars import Country
from uk_election_timetables.election_ids import from_election_id


def get_election_timetable(slug, territory):
    country = {
        "ENG": Country.ENGLAND,
        "WLS": Country.WALES,
        "SCT": Country.SCOTLAND,
        "NIR": Country.NORTHERN_IRELAND,
    }

    if slug.startswith("local") and territory not in country:
        return None

    try:
        return from_election_id(slug, country[territory])

    except BaseException:
        return None
