EC_API_BASE = "http://search.electoralcommission.org.uk/api/search/Registrations"
EC_EMBLEM_BASE = "http://search.electoralcommission.org.uk/Api/Registrations/Emblems"

# There is no concept of a "default" emblem with The Electoral Commission.
# Each emblem has an ID and candidates pick the emblem when they stand.
# However, there are emblems that a more generic than others, so we try to use
# them for the "default" party emblem. For example, The Labour Party might have
# and emblem for "Labour" and "Welsh Labour". In the majority case, showing the
# "Labour" emblem is the best thing to do.
# Normally we're safe to use the emblem with the lowest numerical ID returned by
# the API for the party, however in the following cases the lowest ID emblem
# isn't the best to use. This is an override for the emblem we will call
# deafult.
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
}
