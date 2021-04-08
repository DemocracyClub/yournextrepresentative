EC_API_BASE = (
    "http://search.electoralcommission.org.uk/api/search/Registrations"
)
EC_EMBLEM_BASE = (
    "http://search.electoralcommission.org.uk/Api/Registrations/Emblems"
)

# There is no concept of a "default" emblem with The Electoral Commission.
# Each emblem has an ID and candidates pick the emblem when they stand.
# However, there are emblems that a more generic than others, so we try to use
# them for the "default" party emblem. For example, The Labour Party might have
# and emblem for "Labour" and "Welsh Labour". In the majority case, showing the
# "Labour" emblem is the best thing to do.
# Normally we're safe to use the emblem with the lowest numerical ID returned by
# the API for the party, however in the following cases the lowest ID emblem
# isn't the best to use. This is an override for the emblem we will call
# default.
DEFAULT_EMBLEMS = {
    # Labour Party
    "PP53": 52,
    # Green Party
    "PP63": 1119,
    # Another Green Party
    "PP305": 3540,
    # Plaid Cymru
    "PP77": 2391,
    # Ulster Unionist Party
    "PP83": 807,
    # Trade Unionist and Socialist Coalition
    "PP804": 606,
    # Socialist Labour Party
    "PP73": 81,
    # National Front
    "PP2707": 1204,
    # Christian Party
    "PP2893": 1292,
    # Democratic Unionist Party D.U.P
    "PP70": 78,
    # BNP
    "PP3960": 2380,
    # Liberal party
    "PP54": 54,
    # Animal Welfare Party
    "PP616": 3535,
    # Heavy Woollen District Independents
    "PP6453": 4907,
    # Reform UK
    "PP7931": 7762,
    # All for Unity Unity Party
    "PP12579": 7697,
}

JOINT_DESCRIPTION_REGEX = r"^(.*?) \(joint descriptions? with\s?(.*)\)"

# We change some party names in descriptions. This is because we assume the
# description contains the sub-party name (see `JOINT_DESCRIPTION_REGEX`)
# exactly as written, however in the following cases we need to correct this.
# This is only used for matching descriptions to parties
CORRECTED_PARTY_NAMES_IN_DESC = {
    "The Christian Party Christian Peoples Alliance": "Christian Party Christian Peoples Alliance",
    "St. George's Independents": "Weybridge & St. George's Independents",
    "English Democrats Party": "English Democrats",
    "Tattenhams' Residents' Association": "Tattenhams Residents' Association",
    "Trade Unionists and Socialists Coalition": "Trade Unionist and Socialist Coalition",
    "Molesey Residents Association": "The Molesey Residents Association",
}

# The register is self-inconsistant sometimes, in that a description is approved
# before (sometimes by years) a the joint party is registered.
# This is a mapping of descriptions and the earliest date they can be valid
CORRECTED_DESCRIPTION_DATES = {
    "Ulster Conservatives and Unionists - New Force (Joint Description with Conservative and Unionist Party)": "2001-02-16",
    "Alliance for Democracy (Joint Description with English Democrats Party, and Jury Team)": "2009-03-13",
    "Solidarity - Trade Unionist and Socialist Coalition (Joint Description with Trade Unionist and Socialist Coalition)": "2010-01-27",
}
