import json

current_elections_parents = json.loads(
    """{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "election_id": "local.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Local elections",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": null,
      "group": null,
      "group_type": "election",
      "children": [
        "local.aberdeen-city.2018-02-22",
        "local.aberdeenshire.2018-02-22",
        "local.adur.2018-02-22",
        "local.angus.2018-02-22",
        "local.bedford.2018-02-22",
        "local.brent.2018-02-22",
        "local.bromley.2018-02-22",
        "local.daventry.2018-02-22",
        "local.denbighshire.2018-02-22",
        "local.eden.2018-02-22"
      ],
      "elected_role": null,
      "seats_contested": null,
      "division": null,
      "voting_system": null,
      "current": true,
      "explanation": null,
      "cancelled": false
    }
  ]
}
"""
)
current_elections = json.loads(
    """
{
  "count": 518,
  "next": "https://elections.democracyclub.org.uk/api/elections/?exclude_election_id_regex=%5Eref%5C..%2A&poll_open_date__gte=fakedate&limit=100&offset=100",
  "previous": null,
  "results": [
    {
      "election_id": "local.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Adur local election",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ADU",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Adur District Council",
        "common_name": "Adur",
        "gss": "E07000223",
        "slug": "adur",
        "territory_code": "ENG",
        "election_name": "Adur local election"
      },
      "group": null,
      "group_type": "election",
      "children": [
        "local.aberdeen-city.2018-02-22",
        "local.aberdeenshire.2018-02-22",
        "local.adur.2018-02-22",
        "local.angus.2018-02-22",
        "local.bedford.2018-02-22",
        "local.brent.2018-02-22",
        "local.bromley.2018-02-22",
        "local.daventry.2018-02-22",
        "local.denbighshire.2018-02-22",
        "local.eden.2018-02-22",
        "local.epsom-and-ewell.2018-02-22",
        "local.hertfordshire.2018-02-22",
        "local.high-peak.2018-02-22",
        "local.mid-suffolk.2018-02-22",
        "local.north-warwickshire.2018-02-22",
        "local.rochdale.2018-02-22",
        "local.rochford.2018-02-22",
        "local.rother.2018-02-22",
        "local.south-hams.2018-02-22",
        "local.south-holland.2018-02-22",
        "local.warrington.2018-02-22"
      ],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": null,
      "voting_system": null,
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeen-city.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeen City local election",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABE",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeen City Council",
        "common_name": "Aberdeen City",
        "gss": "S12000033",
        "slug": "aberdeen-city",
        "territory_code": "SCT",
        "election_name": "Aberdeen City local election"
      },
      "group": "local.2018-02-22",
      "group_type": "organisation",
      "children": [
        "local.aberdeen-city.airyhallbroomhillgarthdee.2018-02-22",
        "local.aberdeen-city.bridge-of-don.2018-02-22",
        "local.aberdeen-city.dycebucksburndanestone.2018-02-22",
        "local.aberdeen-city.george-stharbour.2018-02-22",
        "local.aberdeen-city.hazleheadqueens-crosscountesswells.2018-02-22",
        "local.aberdeen-city.hiltonwoodsidestockethill.2018-02-22",
        "local.aberdeen-city.kincorthniggcove.2018-02-22",
        "local.aberdeen-city.kingswellssheddocksleysummerhill.2018-02-22",
        "local.aberdeen-city.lower-deeside.2018-02-22",
        "local.aberdeen-city.midstocketrosemount.2018-02-22",
        "local.aberdeen-city.northfieldmastrick-north.2018-02-22",
        "local.aberdeen-city.tillydroneseatonold-aberdeen.2018-02-22",
        "local.aberdeen-city.torryferryhill.2018-02-22"
      ],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": null,
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeen-city.airyhallbroomhillgarthdee.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeen City local election Airyhall/Broomhill/Garthdee",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABE",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeen City Council",
        "common_name": "Aberdeen City",
        "gss": "S12000033",
        "slug": "aberdeen-city",
        "territory_code": "SCT",
        "election_name": "Aberdeen City local election"
      },
      "group": "local.aberdeen-city.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/265/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeen_city/",
          "short_title": "The Aberdeen City (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Airyhall/Broomhill/Garthdee",
        "official_identifier": "ABE:airyhallbroomhillgarthdee",
        "slug": "airyhallbroomhillgarthdee",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 3,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeen-city.bridge-of-don.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeen City local election Bridge of Don",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABE",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeen City Council",
        "common_name": "Aberdeen City",
        "gss": "S12000033",
        "slug": "aberdeen-city",
        "territory_code": "SCT",
        "election_name": "Aberdeen City local election"
      },
      "group": "local.aberdeen-city.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/265/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeen_city/",
          "short_title": "The Aberdeen City (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Bridge of Don",
        "official_identifier": "ABE:bridge-of-don",
        "slug": "bridge-of-don",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeen-city.dycebucksburndanestone.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeen City local election Dyce/Bucksburn/Danestone",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABE",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeen City Council",
        "common_name": "Aberdeen City",
        "gss": "S12000033",
        "slug": "aberdeen-city",
        "territory_code": "SCT",
        "election_name": "Aberdeen City local election"
      },
      "group": "local.aberdeen-city.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/265/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeen_city/",
          "short_title": "The Aberdeen City (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Dyce/Bucksburn/Danestone",
        "official_identifier": "ABE:dycebucksburndanestone",
        "slug": "dycebucksburndanestone",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeen-city.george-stharbour.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeen City local election George St/Harbour",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABE",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeen City Council",
        "common_name": "Aberdeen City",
        "gss": "S12000033",
        "slug": "aberdeen-city",
        "territory_code": "SCT",
        "election_name": "Aberdeen City local election"
      },
      "group": "local.aberdeen-city.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/265/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeen_city/",
          "short_title": "The Aberdeen City (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "George St/Harbour",
        "official_identifier": "ABE:george-stharbour",
        "slug": "george-stharbour",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeen-city.hazleheadqueens-crosscountesswells.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeen City local election Hazlehead/Queens Cross/Countesswells",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABE",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeen City Council",
        "common_name": "Aberdeen City",
        "gss": "S12000033",
        "slug": "aberdeen-city",
        "territory_code": "SCT",
        "election_name": "Aberdeen City local election"
      },
      "group": "local.aberdeen-city.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/265/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeen_city/",
          "short_title": "The Aberdeen City (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Hazlehead/Queens Cross/Countesswells",
        "official_identifier": "ABE:hazleheadqueens-crosscountesswells",
        "slug": "hazleheadqueens-crosscountesswells",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeen-city.hiltonwoodsidestockethill.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeen City local election Hilton/Woodside/Stockethill",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABE",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeen City Council",
        "common_name": "Aberdeen City",
        "gss": "S12000033",
        "slug": "aberdeen-city",
        "territory_code": "SCT",
        "election_name": "Aberdeen City local election"
      },
      "group": "local.aberdeen-city.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/265/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeen_city/",
          "short_title": "The Aberdeen City (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Hilton/Woodside/Stockethill",
        "official_identifier": "ABE:hiltonwoodsidestockethill",
        "slug": "hiltonwoodsidestockethill",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 3,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeen-city.kincorthniggcove.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeen City local election Kincorth/Nigg/Cove",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABE",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeen City Council",
        "common_name": "Aberdeen City",
        "gss": "S12000033",
        "slug": "aberdeen-city",
        "territory_code": "SCT",
        "election_name": "Aberdeen City local election"
      },
      "group": "local.aberdeen-city.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/265/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeen_city/",
          "short_title": "The Aberdeen City (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Kincorth/Nigg/Cove",
        "official_identifier": "ABE:kincorthniggcove",
        "slug": "kincorthniggcove",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeen-city.kingswellssheddocksleysummerhill.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeen City local election Kingswells/Sheddocksley/Summerhill",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABE",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeen City Council",
        "common_name": "Aberdeen City",
        "gss": "S12000033",
        "slug": "aberdeen-city",
        "territory_code": "SCT",
        "election_name": "Aberdeen City local election"
      },
      "group": "local.aberdeen-city.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/265/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeen_city/",
          "short_title": "The Aberdeen City (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Kingswells/Sheddocksley/Summerhill",
        "official_identifier": "ABE:kingswellssheddocksleysummerhill",
        "slug": "kingswellssheddocksleysummerhill",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 3,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeen-city.lower-deeside.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeen City local election Lower Deeside",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABE",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeen City Council",
        "common_name": "Aberdeen City",
        "gss": "S12000033",
        "slug": "aberdeen-city",
        "territory_code": "SCT",
        "election_name": "Aberdeen City local election"
      },
      "group": "local.aberdeen-city.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/265/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeen_city/",
          "short_title": "The Aberdeen City (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Lower Deeside",
        "official_identifier": "ABE:lower-deeside",
        "slug": "lower-deeside",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 3,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeen-city.midstocketrosemount.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeen City local election Midstocket/Rosemount",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABE",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeen City Council",
        "common_name": "Aberdeen City",
        "gss": "S12000033",
        "slug": "aberdeen-city",
        "territory_code": "SCT",
        "election_name": "Aberdeen City local election"
      },
      "group": "local.aberdeen-city.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/265/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeen_city/",
          "short_title": "The Aberdeen City (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Midstocket/Rosemount",
        "official_identifier": "ABE:midstocketrosemount",
        "slug": "midstocketrosemount",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 3,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeen-city.northfieldmastrick-north.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeen City local election Northfield/Mastrick North",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABE",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeen City Council",
        "common_name": "Aberdeen City",
        "gss": "S12000033",
        "slug": "aberdeen-city",
        "territory_code": "SCT",
        "election_name": "Aberdeen City local election"
      },
      "group": "local.aberdeen-city.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/265/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeen_city/",
          "short_title": "The Aberdeen City (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Northfield/Mastrick North",
        "official_identifier": "ABE:northfieldmastrick-north",
        "slug": "northfieldmastrick-north",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 3,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeen-city.tillydroneseatonold-aberdeen.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeen City local election Tillydrone/Seaton/Old Aberdeen",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABE",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeen City Council",
        "common_name": "Aberdeen City",
        "gss": "S12000033",
        "slug": "aberdeen-city",
        "territory_code": "SCT",
        "election_name": "Aberdeen City local election"
      },
      "group": "local.aberdeen-city.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/265/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeen_city/",
          "short_title": "The Aberdeen City (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Tillydrone/Seaton/Old Aberdeen",
        "official_identifier": "ABE:tillydroneseatonold-aberdeen",
        "slug": "tillydroneseatonold-aberdeen",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 3,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeen-city.torryferryhill.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeen City local election Torry/Ferryhill",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABE",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeen City Council",
        "common_name": "Aberdeen City",
        "gss": "S12000033",
        "slug": "aberdeen-city",
        "territory_code": "SCT",
        "election_name": "Aberdeen City local election"
      },
      "group": "local.aberdeen-city.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/265/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeen_city/",
          "short_title": "The Aberdeen City (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Torry/Ferryhill",
        "official_identifier": "ABE:torryferryhill",
        "slug": "torryferryhill",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeenshire.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeenshire local election",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeenshire Council",
        "common_name": "Aberdeenshire",
        "gss": "S12000034",
        "slug": "aberdeenshire",
        "territory_code": "SCT",
        "election_name": "Aberdeenshire local election"
      },
      "group": "local.2018-02-22",
      "group_type": "organisation",
      "children": [
        "local.aberdeenshire.aboyne-upper-deeside-and-donside.2018-02-22",
        "local.aberdeenshire.banchory-and-mid-deeside.2018-02-22",
        "local.aberdeenshire.banff-and-district.2018-02-22",
        "local.aberdeenshire.central-buchan.2018-02-22",
        "local.aberdeenshire.east-garioch.2018-02-22",
        "local.aberdeenshire.ellon-and-district.2018-02-22",
        "local.aberdeenshire.fraserburgh-and-district.2018-02-22",
        "local.aberdeenshire.huntly-strathbogie-and-howe-of-alford.2018-02-22",
        "local.aberdeenshire.inverurie-and-district.2018-02-22",
        "local.aberdeenshire.mearns.2018-02-22",
        "local.aberdeenshire.mid-formartine.2018-02-22",
        "local.aberdeenshire.north-kincardine.2018-02-22",
        "local.aberdeenshire.peterhead-north-and-rattray.2018-02-22",
        "local.aberdeenshire.peterhead-south-and-cruden.2018-02-22",
        "local.aberdeenshire.stonehaven-and-lower-deeside.2018-02-22",
        "local.aberdeenshire.troup.2018-02-22",
        "local.aberdeenshire.turriff-and-district.2018-02-22",
        "local.aberdeenshire.west-garioch.2018-02-22",
        "local.aberdeenshire.westhill-and-district.2018-02-22"
      ],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": null,
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeenshire.aboyne-upper-deeside-and-donside.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeenshire local election Aboyne, Upper Deeside and Donside",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeenshire Council",
        "common_name": "Aberdeenshire",
        "gss": "S12000034",
        "slug": "aberdeenshire",
        "territory_code": "SCT",
        "election_name": "Aberdeenshire local election"
      },
      "group": "local.aberdeenshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/266/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeenshire/",
          "short_title": "The Aberdeenshire (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Aboyne, Upper Deeside and Donside",
        "official_identifier": "ABD:aboyne-upper-deeside-and-donside",
        "slug": "aboyne-upper-deeside-and-donside",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 3,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeenshire.banchory-and-mid-deeside.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeenshire local election Banchory and Mid Deeside",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeenshire Council",
        "common_name": "Aberdeenshire",
        "gss": "S12000034",
        "slug": "aberdeenshire",
        "territory_code": "SCT",
        "election_name": "Aberdeenshire local election"
      },
      "group": "local.aberdeenshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/266/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeenshire/",
          "short_title": "The Aberdeenshire (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Banchory and Mid Deeside",
        "official_identifier": "ABD:banchory-and-mid-deeside",
        "slug": "banchory-and-mid-deeside",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 3,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeenshire.banff-and-district.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeenshire local election Banff and District",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeenshire Council",
        "common_name": "Aberdeenshire",
        "gss": "S12000034",
        "slug": "aberdeenshire",
        "territory_code": "SCT",
        "election_name": "Aberdeenshire local election"
      },
      "group": "local.aberdeenshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/266/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeenshire/",
          "short_title": "The Aberdeenshire (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Banff and District",
        "official_identifier": "ABD:banff-and-district",
        "slug": "banff-and-district",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 3,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeenshire.central-buchan.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeenshire local election Central Buchan",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeenshire Council",
        "common_name": "Aberdeenshire",
        "gss": "S12000034",
        "slug": "aberdeenshire",
        "territory_code": "SCT",
        "election_name": "Aberdeenshire local election"
      },
      "group": "local.aberdeenshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/266/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeenshire/",
          "short_title": "The Aberdeenshire (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Central Buchan",
        "official_identifier": "ABD:central-buchan",
        "slug": "central-buchan",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeenshire.east-garioch.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeenshire local election East Garioch",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeenshire Council",
        "common_name": "Aberdeenshire",
        "gss": "S12000034",
        "slug": "aberdeenshire",
        "territory_code": "SCT",
        "election_name": "Aberdeenshire local election"
      },
      "group": "local.aberdeenshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/266/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeenshire/",
          "short_title": "The Aberdeenshire (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "East Garioch",
        "official_identifier": "ABD:east-garioch",
        "slug": "east-garioch",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeenshire.ellon-and-district.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeenshire local election Ellon and District",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeenshire Council",
        "common_name": "Aberdeenshire",
        "gss": "S12000034",
        "slug": "aberdeenshire",
        "territory_code": "SCT",
        "election_name": "Aberdeenshire local election"
      },
      "group": "local.aberdeenshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/266/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeenshire/",
          "short_title": "The Aberdeenshire (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Ellon and District",
        "official_identifier": "ABD:ellon-and-district",
        "slug": "ellon-and-district",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeenshire.fraserburgh-and-district.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeenshire local election Fraserburgh and District",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeenshire Council",
        "common_name": "Aberdeenshire",
        "gss": "S12000034",
        "slug": "aberdeenshire",
        "territory_code": "SCT",
        "election_name": "Aberdeenshire local election"
      },
      "group": "local.aberdeenshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/266/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeenshire/",
          "short_title": "The Aberdeenshire (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Fraserburgh and District",
        "official_identifier": "ABD:fraserburgh-and-district",
        "slug": "fraserburgh-and-district",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeenshire.huntly-strathbogie-and-howe-of-alford.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeenshire local election Huntly, Strathbogie and Howe of Alford",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeenshire Council",
        "common_name": "Aberdeenshire",
        "gss": "S12000034",
        "slug": "aberdeenshire",
        "territory_code": "SCT",
        "election_name": "Aberdeenshire local election"
      },
      "group": "local.aberdeenshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/266/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeenshire/",
          "short_title": "The Aberdeenshire (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Huntly, Strathbogie and Howe of Alford",
        "official_identifier": "ABD:huntly-strathbogie-and-howe-of-alford",
        "slug": "huntly-strathbogie-and-howe-of-alford",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeenshire.inverurie-and-district.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeenshire local election Inverurie and District",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeenshire Council",
        "common_name": "Aberdeenshire",
        "gss": "S12000034",
        "slug": "aberdeenshire",
        "territory_code": "SCT",
        "election_name": "Aberdeenshire local election"
      },
      "group": "local.aberdeenshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/266/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeenshire/",
          "short_title": "The Aberdeenshire (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Inverurie and District",
        "official_identifier": "ABD:inverurie-and-district",
        "slug": "inverurie-and-district",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeenshire.mearns.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeenshire local election Mearns",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeenshire Council",
        "common_name": "Aberdeenshire",
        "gss": "S12000034",
        "slug": "aberdeenshire",
        "territory_code": "SCT",
        "election_name": "Aberdeenshire local election"
      },
      "group": "local.aberdeenshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/266/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeenshire/",
          "short_title": "The Aberdeenshire (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Mearns",
        "official_identifier": "ABD:mearns",
        "slug": "mearns",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeenshire.mid-formartine.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeenshire local election Mid Formartine",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeenshire Council",
        "common_name": "Aberdeenshire",
        "gss": "S12000034",
        "slug": "aberdeenshire",
        "territory_code": "SCT",
        "election_name": "Aberdeenshire local election"
      },
      "group": "local.aberdeenshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/266/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeenshire/",
          "short_title": "The Aberdeenshire (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Mid Formartine",
        "official_identifier": "ABD:mid-formartine",
        "slug": "mid-formartine",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeenshire.north-kincardine.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeenshire local election North Kincardine",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeenshire Council",
        "common_name": "Aberdeenshire",
        "gss": "S12000034",
        "slug": "aberdeenshire",
        "territory_code": "SCT",
        "election_name": "Aberdeenshire local election"
      },
      "group": "local.aberdeenshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/266/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeenshire/",
          "short_title": "The Aberdeenshire (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "North Kincardine",
        "official_identifier": "ABD:north-kincardine",
        "slug": "north-kincardine",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeenshire.peterhead-north-and-rattray.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeenshire local election Peterhead North and Rattray",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeenshire Council",
        "common_name": "Aberdeenshire",
        "gss": "S12000034",
        "slug": "aberdeenshire",
        "territory_code": "SCT",
        "election_name": "Aberdeenshire local election"
      },
      "group": "local.aberdeenshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/266/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeenshire/",
          "short_title": "The Aberdeenshire (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Peterhead North and Rattray",
        "official_identifier": "ABD:peterhead-north-and-rattray",
        "slug": "peterhead-north-and-rattray",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeenshire.peterhead-south-and-cruden.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeenshire local election Peterhead South and Cruden",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeenshire Council",
        "common_name": "Aberdeenshire",
        "gss": "S12000034",
        "slug": "aberdeenshire",
        "territory_code": "SCT",
        "election_name": "Aberdeenshire local election"
      },
      "group": "local.aberdeenshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/266/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeenshire/",
          "short_title": "The Aberdeenshire (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Peterhead South and Cruden",
        "official_identifier": "ABD:peterhead-south-and-cruden",
        "slug": "peterhead-south-and-cruden",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 3,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeenshire.stonehaven-and-lower-deeside.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeenshire local election Stonehaven and Lower Deeside",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeenshire Council",
        "common_name": "Aberdeenshire",
        "gss": "S12000034",
        "slug": "aberdeenshire",
        "territory_code": "SCT",
        "election_name": "Aberdeenshire local election"
      },
      "group": "local.aberdeenshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/266/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeenshire/",
          "short_title": "The Aberdeenshire (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Stonehaven and Lower Deeside",
        "official_identifier": "ABD:stonehaven-and-lower-deeside",
        "slug": "stonehaven-and-lower-deeside",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeenshire.troup.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeenshire local election Troup",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeenshire Council",
        "common_name": "Aberdeenshire",
        "gss": "S12000034",
        "slug": "aberdeenshire",
        "territory_code": "SCT",
        "election_name": "Aberdeenshire local election"
      },
      "group": "local.aberdeenshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/266/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeenshire/",
          "short_title": "The Aberdeenshire (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Troup",
        "official_identifier": "ABD:troup",
        "slug": "troup",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 3,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeenshire.turriff-and-district.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeenshire local election Turriff and District",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeenshire Council",
        "common_name": "Aberdeenshire",
        "gss": "S12000034",
        "slug": "aberdeenshire",
        "territory_code": "SCT",
        "election_name": "Aberdeenshire local election"
      },
      "group": "local.aberdeenshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/266/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeenshire/",
          "short_title": "The Aberdeenshire (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Turriff and District",
        "official_identifier": "ABD:turriff-and-district",
        "slug": "turriff-and-district",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeenshire.west-garioch.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeenshire local election West Garioch",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeenshire Council",
        "common_name": "Aberdeenshire",
        "gss": "S12000034",
        "slug": "aberdeenshire",
        "territory_code": "SCT",
        "election_name": "Aberdeenshire local election"
      },
      "group": "local.aberdeenshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/266/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeenshire/",
          "short_title": "The Aberdeenshire (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "West Garioch",
        "official_identifier": "ABD:west-garioch",
        "slug": "west-garioch",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 3,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.aberdeenshire.westhill-and-district.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Aberdeenshire local election Westhill and District",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ABD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Aberdeenshire Council",
        "common_name": "Aberdeenshire",
        "gss": "S12000034",
        "slug": "aberdeenshire",
        "territory_code": "SCT",
        "election_name": "Aberdeenshire local election"
      },
      "group": "local.aberdeenshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/266/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/aberdeenshire/",
          "short_title": "The Aberdeenshire (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Westhill and District",
        "official_identifier": "ABD:westhill-and-district",
        "slug": "westhill-and-district",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.adur.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Adur local election",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ADU",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Adur District Council",
        "common_name": "Adur",
        "gss": "E07000223",
        "slug": "adur",
        "territory_code": "ENG",
        "election_name": "Adur local election"
      },
      "group": "local.2018-02-22",
      "group_type": "organisation",
      "children": [
        "local.adur.buckingham.2018-02-22",
        "local.adur.churchill.2018-02-22",
        "local.adur.cokeham.2018-02-22",
        "local.adur.eastbrook.2018-02-22",
        "local.adur.hillside.2018-02-22",
        "local.adur.manor.2018-02-22",
        "local.adur.marine.2018-02-22",
        "local.adur.mash-barn.2018-02-22",
        "local.adur.peverel.2018-02-22",
        "local.adur.southlands.2018-02-22",
        "local.adur.southwick-green.2018-02-22",
        "local.adur.st-marys.2018-02-22",
        "local.adur.st-nicolas.2018-02-22",
        "local.adur.widewater.2018-02-22"
      ],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": null,
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.adur.buckingham.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Adur local election Buckingham",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ADU",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Adur District Council",
        "common_name": "Adur",
        "gss": "E07000223",
        "slug": "adur",
        "territory_code": "ENG",
        "election_name": "Adur local election"
      },
      "group": "local.adur.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Buckingham",
        "official_identifier": "gss:E05007562",
        "slug": "buckingham",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.adur.churchill.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Adur local election Churchill",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ADU",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Adur District Council",
        "common_name": "Adur",
        "gss": "E07000223",
        "slug": "adur",
        "territory_code": "ENG",
        "election_name": "Adur local election"
      },
      "group": "local.adur.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Churchill",
        "official_identifier": "gss:E05007563",
        "slug": "churchill",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.adur.cokeham.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Adur local election Cokeham",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ADU",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Adur District Council",
        "common_name": "Adur",
        "gss": "E07000223",
        "slug": "adur",
        "territory_code": "ENG",
        "election_name": "Adur local election"
      },
      "group": "local.adur.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Cokeham",
        "official_identifier": "gss:E05007564",
        "slug": "cokeham",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.adur.eastbrook.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Adur local election Eastbrook",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ADU",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Adur District Council",
        "common_name": "Adur",
        "gss": "E07000223",
        "slug": "adur",
        "territory_code": "ENG",
        "election_name": "Adur local election"
      },
      "group": "local.adur.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Eastbrook",
        "official_identifier": "gss:E05007565",
        "slug": "eastbrook",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.adur.hillside.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Adur local election Hillside",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ADU",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Adur District Council",
        "common_name": "Adur",
        "gss": "E07000223",
        "slug": "adur",
        "territory_code": "ENG",
        "election_name": "Adur local election"
      },
      "group": "local.adur.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Hillside",
        "official_identifier": "gss:E05007566",
        "slug": "hillside",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.adur.manor.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Adur local election Manor",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ADU",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Adur District Council",
        "common_name": "Adur",
        "gss": "E07000223",
        "slug": "adur",
        "territory_code": "ENG",
        "election_name": "Adur local election"
      },
      "group": "local.adur.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Manor",
        "official_identifier": "gss:E05007567",
        "slug": "manor",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.adur.marine.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Adur local election Marine",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ADU",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Adur District Council",
        "common_name": "Adur",
        "gss": "E07000223",
        "slug": "adur",
        "territory_code": "ENG",
        "election_name": "Adur local election"
      },
      "group": "local.adur.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Marine",
        "official_identifier": "gss:E05007568",
        "slug": "marine",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.adur.mash-barn.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Adur local election Mash Barn",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ADU",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Adur District Council",
        "common_name": "Adur",
        "gss": "E07000223",
        "slug": "adur",
        "territory_code": "ENG",
        "election_name": "Adur local election"
      },
      "group": "local.adur.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Mash Barn",
        "official_identifier": "gss:E05007569",
        "slug": "mash-barn",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.adur.peverel.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Adur local election Peverel",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ADU",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Adur District Council",
        "common_name": "Adur",
        "gss": "E07000223",
        "slug": "adur",
        "territory_code": "ENG",
        "election_name": "Adur local election"
      },
      "group": "local.adur.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Peverel",
        "official_identifier": "gss:E05007570",
        "slug": "peverel",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.adur.southlands.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Adur local election Southlands",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ADU",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Adur District Council",
        "common_name": "Adur",
        "gss": "E07000223",
        "slug": "adur",
        "territory_code": "ENG",
        "election_name": "Adur local election"
      },
      "group": "local.adur.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Southlands",
        "official_identifier": "gss:E05007573",
        "slug": "southlands",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.adur.southwick-green.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Adur local election Southwick Green",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ADU",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Adur District Council",
        "common_name": "Adur",
        "gss": "E07000223",
        "slug": "adur",
        "territory_code": "ENG",
        "election_name": "Adur local election"
      },
      "group": "local.adur.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Southwick Green",
        "official_identifier": "gss:E05007574",
        "slug": "southwick-green",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.adur.st-marys.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Adur local election St Mary's",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ADU",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Adur District Council",
        "common_name": "Adur",
        "gss": "E07000223",
        "slug": "adur",
        "territory_code": "ENG",
        "election_name": "Adur local election"
      },
      "group": "local.adur.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "St Mary's",
        "official_identifier": "gss:E05007571",
        "slug": "st-marys",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.adur.st-nicolas.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Adur local election St Nicolas",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ADU",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Adur District Council",
        "common_name": "Adur",
        "gss": "E07000223",
        "slug": "adur",
        "territory_code": "ENG",
        "election_name": "Adur local election"
      },
      "group": "local.adur.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "St Nicolas",
        "official_identifier": "gss:E05007572",
        "slug": "st-nicolas",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.adur.widewater.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Adur local election Widewater",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ADU",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Adur District Council",
        "common_name": "Adur",
        "gss": "E07000223",
        "slug": "adur",
        "territory_code": "ENG",
        "election_name": "Adur local election"
      },
      "group": "local.adur.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Widewater",
        "official_identifier": "gss:E05007575",
        "slug": "widewater",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.angus.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Angus local election",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ANS",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Angus Council",
        "common_name": "Angus",
        "gss": "S12000041",
        "slug": "angus",
        "territory_code": "SCT",
        "election_name": "Angus local election"
      },
      "group": "local.2018-02-22",
      "group_type": "organisation",
      "children": [
        "local.angus.arbroath-east-and-lunan.2018-02-22",
        "local.angus.arbroath-west-letham-and-friockheim.2018-02-22",
        "local.angus.brechin-and-edzell.2018-02-22",
        "local.angus.carnoustie-and-district.2018-02-22",
        "local.angus.forfar-and-district.2018-02-22",
        "local.angus.kirriemuir-and-dean.2018-02-22",
        "local.angus.monifieth-and-sidlaw.2018-02-22",
        "local.angus.montrose-and-district.2018-02-22"
      ],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": null,
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.angus.arbroath-east-and-lunan.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Angus local election Arbroath East and Lunan",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ANS",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Angus Council",
        "common_name": "Angus",
        "gss": "S12000041",
        "slug": "angus",
        "territory_code": "SCT",
        "election_name": "Angus local election"
      },
      "group": "local.angus.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/267/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/angus/",
          "short_title": "The Angus (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Arbroath East and Lunan",
        "official_identifier": "ANS:arbroath-east-and-lunan",
        "slug": "arbroath-east-and-lunan",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 3,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.angus.arbroath-west-letham-and-friockheim.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Angus local election Arbroath West, Letham and Friockheim",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ANS",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Angus Council",
        "common_name": "Angus",
        "gss": "S12000041",
        "slug": "angus",
        "territory_code": "SCT",
        "election_name": "Angus local election"
      },
      "group": "local.angus.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/267/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/angus/",
          "short_title": "The Angus (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Arbroath West, Letham and Friockheim",
        "official_identifier": "ANS:arbroath-west-letham-and-friockheim",
        "slug": "arbroath-west-letham-and-friockheim",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.angus.brechin-and-edzell.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Angus local election Brechin and Edzell",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ANS",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Angus Council",
        "common_name": "Angus",
        "gss": "S12000041",
        "slug": "angus",
        "territory_code": "SCT",
        "election_name": "Angus local election"
      },
      "group": "local.angus.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/267/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/angus/",
          "short_title": "The Angus (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Brechin and Edzell",
        "official_identifier": "ANS:brechin-and-edzell",
        "slug": "brechin-and-edzell",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 3,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.angus.carnoustie-and-district.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Angus local election Carnoustie and District",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ANS",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Angus Council",
        "common_name": "Angus",
        "gss": "S12000041",
        "slug": "angus",
        "territory_code": "SCT",
        "election_name": "Angus local election"
      },
      "group": "local.angus.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/267/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/angus/",
          "short_title": "The Angus (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Carnoustie and District",
        "official_identifier": "ANS:carnoustie-and-district",
        "slug": "carnoustie-and-district",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 3,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.angus.forfar-and-district.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Angus local election Forfar and District",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ANS",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Angus Council",
        "common_name": "Angus",
        "gss": "S12000041",
        "slug": "angus",
        "territory_code": "SCT",
        "election_name": "Angus local election"
      },
      "group": "local.angus.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/267/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/angus/",
          "short_title": "The Angus (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Forfar and District",
        "official_identifier": "ANS:forfar-and-district",
        "slug": "forfar-and-district",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.angus.kirriemuir-and-dean.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Angus local election Kirriemuir and Dean",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ANS",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Angus Council",
        "common_name": "Angus",
        "gss": "S12000041",
        "slug": "angus",
        "territory_code": "SCT",
        "election_name": "Angus local election"
      },
      "group": "local.angus.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/267/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/angus/",
          "short_title": "The Angus (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Kirriemuir and Dean",
        "official_identifier": "ANS:kirriemuir-and-dean",
        "slug": "kirriemuir-and-dean",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 3,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.angus.monifieth-and-sidlaw.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Angus local election Monifieth and Sidlaw",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ANS",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Angus Council",
        "common_name": "Angus",
        "gss": "S12000041",
        "slug": "angus",
        "territory_code": "SCT",
        "election_name": "Angus local election"
      },
      "group": "local.angus.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/267/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/angus/",
          "short_title": "The Angus (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Monifieth and Sidlaw",
        "official_identifier": "ANS:monifieth-and-sidlaw",
        "slug": "monifieth-and-sidlaw",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.angus.montrose-and-district.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Angus local election Montrose and District",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ANS",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Angus Council",
        "common_name": "Angus",
        "gss": "S12000041",
        "slug": "angus",
        "territory_code": "SCT",
        "election_name": "Angus local election"
      },
      "group": "local.angus.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/267/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/angus/",
          "short_title": "The Angus (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Montrose and District",
        "official_identifier": "ANS:montrose-and-district",
        "slug": "montrose-and-district",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.2018-02-22",
      "group_type": "organisation",
      "children": [
        "local.bedford.brickhill.2018-02-22",
        "local.bedford.bromham-and-biddenham.2018-02-22",
        "local.bedford.castle.2018-02-22",
        "local.bedford.cauldwell.2018-02-22",
        "local.bedford.clapham.2018-02-22",
        "local.bedford.de-parys.2018-02-22",
        "local.bedford.eastcotts.2018-02-22",
        "local.bedford.elstow-and-stewartby.2018-02-22",
        "local.bedford.goldington.2018-02-22",
        "local.bedford.great-barford.2018-02-22",
        "local.bedford.harpur.2018-02-22",
        "local.bedford.harrold.2018-02-22",
        "local.bedford.kempston-central-and-east.2018-02-22",
        "local.bedford.kempston-north.2018-02-22",
        "local.bedford.kempston-rural.2018-02-22",
        "local.bedford.kempston-south.2018-02-22",
        "local.bedford.kempston-west.2018-02-22",
        "local.bedford.kingsbrook.2018-02-22",
        "local.bedford.newnham.2018-02-22",
        "local.bedford.oakley.2018-02-22",
        "local.bedford.putnoe.2018-02-22",
        "local.bedford.queens-park.2018-02-22",
        "local.bedford.riseley.2018-02-22",
        "local.bedford.sharnbrook.2018-02-22",
        "local.bedford.wilshamstead.2018-02-22",
        "local.bedford.wootton.2018-02-22",
        "local.bedford.wyboston.2018-02-22"
      ],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": null,
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.brickhill.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Brickhill",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Brickhill",
        "official_identifier": "gss:E05008751",
        "slug": "brickhill",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.bromham-and-biddenham.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Bromham and Biddenham",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Bromham and Biddenham",
        "official_identifier": "gss:E05008752",
        "slug": "bromham-and-biddenham",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.castle.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Castle",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Castle",
        "official_identifier": "gss:E05008753",
        "slug": "castle",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.cauldwell.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Cauldwell",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Cauldwell",
        "official_identifier": "gss:E05008754",
        "slug": "cauldwell",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.clapham.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Clapham",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Clapham",
        "official_identifier": "gss:E05008755",
        "slug": "clapham",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.de-parys.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election De Parys",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "De Parys",
        "official_identifier": "gss:E05008756",
        "slug": "de-parys",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.eastcotts.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Eastcotts",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Eastcotts",
        "official_identifier": "gss:E05008757",
        "slug": "eastcotts",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.elstow-and-stewartby.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Elstow and Stewartby",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Elstow and Stewartby",
        "official_identifier": "gss:E05008758",
        "slug": "elstow-and-stewartby",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.goldington.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Goldington",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Goldington",
        "official_identifier": "gss:E05008759",
        "slug": "goldington",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.great-barford.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Great Barford",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Great Barford",
        "official_identifier": "gss:E05008760",
        "slug": "great-barford",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.harpur.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Harpur",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Harpur",
        "official_identifier": "gss:E05008761",
        "slug": "harpur",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.harrold.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Harrold",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Harrold",
        "official_identifier": "gss:E05008762",
        "slug": "harrold",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.kempston-central-and-east.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Kempston Central and East",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Kempston Central and East",
        "official_identifier": "gss:E05008763",
        "slug": "kempston-central-and-east",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.kempston-north.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Kempston North",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Kempston North",
        "official_identifier": "gss:E05008764",
        "slug": "kempston-north",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.kempston-rural.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Kempston Rural",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Kempston Rural",
        "official_identifier": "gss:E05008765",
        "slug": "kempston-rural",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.kempston-south.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Kempston South",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Kempston South",
        "official_identifier": "gss:E05008766",
        "slug": "kempston-south",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.kempston-west.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Kempston West",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Kempston West",
        "official_identifier": "gss:E05008767",
        "slug": "kempston-west",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.kingsbrook.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Kingsbrook",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Kingsbrook",
        "official_identifier": "gss:E05008768",
        "slug": "kingsbrook",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.newnham.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Newnham",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Newnham",
        "official_identifier": "gss:E05008769",
        "slug": "newnham",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.oakley.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Oakley",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Oakley",
        "official_identifier": "gss:E05008770",
        "slug": "oakley",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.putnoe.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Putnoe",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Putnoe",
        "official_identifier": "gss:E05008771",
        "slug": "putnoe",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.queens-park.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Queens Park",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Queens Park",
        "official_identifier": "gss:E05008772",
        "slug": "queens-park",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.riseley.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Riseley",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Riseley",
        "official_identifier": "gss:E05008773",
        "slug": "riseley",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.sharnbrook.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Sharnbrook",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Sharnbrook",
        "official_identifier": "gss:E05008774",
        "slug": "sharnbrook",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.wilshamstead.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Wilshamstead",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Wilshamstead",
        "official_identifier": "gss:E05008775",
        "slug": "wilshamstead",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.wootton.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Wootton",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Wootton",
        "official_identifier": "gss:E05008776",
        "slug": "wootton",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bedford.wyboston.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bedford local election Wyboston",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BDF",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Bedford Borough Council",
        "common_name": "Bedford",
        "gss": "E06000055",
        "slug": "bedford",
        "territory_code": "ENG",
        "election_name": "Bedford local election"
      },
      "group": "local.bedford.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2011-01-28",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2011 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Wyboston",
        "official_identifier": "gss:E05008777",
        "slug": "wyboston",
        "division_type": "UTW",
        "division_subtype": "Unitary Authority ward (UTW)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.brent.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Brent local election",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Brent",
        "common_name": "Brent",
        "gss": "E09000005",
        "slug": "brent",
        "territory_code": "ENG",
        "election_name": "Brent local election"
      },
      "group": "local.2018-02-22",
      "group_type": "organisation",
      "children": [
        "local.brent.alperton.2018-02-22",
        "local.brent.barnhill.2018-02-22",
        "local.brent.brondesbury-park.2018-02-22",
        "local.brent.dollis-hill.2018-02-22",
        "local.brent.dudden-hill.2018-02-22",
        "local.brent.fryent.2018-02-22",
        "local.brent.harlesden.2018-02-22",
        "local.brent.kensal-green.2018-02-22",
        "local.brent.kenton.2018-02-22",
        "local.brent.kilburn.2018-02-22",
        "local.brent.mapesbury.2018-02-22",
        "local.brent.northwick-park.2018-02-22",
        "local.brent.preston.2018-02-22",
        "local.brent.queens-park.2018-02-22",
        "local.brent.queensbury.2018-02-22",
        "local.brent.stonebridge.2018-02-22",
        "local.brent.sudbury.2018-02-22",
        "local.brent.tokyngton.2018-02-22",
        "local.brent.welsh-harp.2018-02-22",
        "local.brent.wembley-central.2018-02-22",
        "local.brent.willesden-green.2018-02-22"
      ],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": null,
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.brent.alperton.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Brent local election Alperton",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Brent",
        "common_name": "Brent",
        "gss": "E09000005",
        "slug": "brent",
        "territory_code": "ENG",
        "election_name": "Brent local election"
      },
      "group": "local.brent.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Alperton",
        "official_identifier": "gss:E05000085",
        "slug": "alperton",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.brent.barnhill.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Brent local election Barnhill",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Brent",
        "common_name": "Brent",
        "gss": "E09000005",
        "slug": "brent",
        "territory_code": "ENG",
        "election_name": "Brent local election"
      },
      "group": "local.brent.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Barnhill",
        "official_identifier": "gss:E05000086",
        "slug": "barnhill",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.brent.brondesbury-park.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Brent local election Brondesbury Park",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Brent",
        "common_name": "Brent",
        "gss": "E09000005",
        "slug": "brent",
        "territory_code": "ENG",
        "election_name": "Brent local election"
      },
      "group": "local.brent.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Brondesbury Park",
        "official_identifier": "gss:E05000087",
        "slug": "brondesbury-park",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.brent.dollis-hill.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Brent local election Dollis Hill",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Brent",
        "common_name": "Brent",
        "gss": "E09000005",
        "slug": "brent",
        "territory_code": "ENG",
        "election_name": "Brent local election"
      },
      "group": "local.brent.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Dollis Hill",
        "official_identifier": "gss:E05000088",
        "slug": "dollis-hill",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.brent.dudden-hill.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Brent local election Dudden Hill",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Brent",
        "common_name": "Brent",
        "gss": "E09000005",
        "slug": "brent",
        "territory_code": "ENG",
        "election_name": "Brent local election"
      },
      "group": "local.brent.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Dudden Hill",
        "official_identifier": "gss:E05000089",
        "slug": "dudden-hill",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.brent.fryent.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Brent local election Fryent",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Brent",
        "common_name": "Brent",
        "gss": "E09000005",
        "slug": "brent",
        "territory_code": "ENG",
        "election_name": "Brent local election"
      },
      "group": "local.brent.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Fryent",
        "official_identifier": "gss:E05000090",
        "slug": "fryent",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.brent.harlesden.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Brent local election Harlesden",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Brent",
        "common_name": "Brent",
        "gss": "E09000005",
        "slug": "brent",
        "territory_code": "ENG",
        "election_name": "Brent local election"
      },
      "group": "local.brent.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Harlesden",
        "official_identifier": "gss:E05000091",
        "slug": "harlesden",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.brent.kensal-green.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Brent local election Kensal Green",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Brent",
        "common_name": "Brent",
        "gss": "E09000005",
        "slug": "brent",
        "territory_code": "ENG",
        "election_name": "Brent local election"
      },
      "group": "local.brent.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Kensal Green",
        "official_identifier": "gss:E05000092",
        "slug": "kensal-green",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.brent.kenton.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Brent local election Kenton",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Brent",
        "common_name": "Brent",
        "gss": "E09000005",
        "slug": "brent",
        "territory_code": "ENG",
        "election_name": "Brent local election"
      },
      "group": "local.brent.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Kenton",
        "official_identifier": "gss:E05000093",
        "slug": "kenton",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.brent.kilburn.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Brent local election Kilburn",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Brent",
        "common_name": "Brent",
        "gss": "E09000005",
        "slug": "brent",
        "territory_code": "ENG",
        "election_name": "Brent local election"
      },
      "group": "local.brent.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Kilburn",
        "official_identifier": "gss:E05000094",
        "slug": "kilburn",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.brent.mapesbury.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Brent local election Mapesbury",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Brent",
        "common_name": "Brent",
        "gss": "E09000005",
        "slug": "brent",
        "territory_code": "ENG",
        "election_name": "Brent local election"
      },
      "group": "local.brent.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Mapesbury",
        "official_identifier": "gss:E05000095",
        "slug": "mapesbury",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.brent.northwick-park.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Brent local election Northwick Park",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Brent",
        "common_name": "Brent",
        "gss": "E09000005",
        "slug": "brent",
        "territory_code": "ENG",
        "election_name": "Brent local election"
      },
      "group": "local.brent.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Northwick Park",
        "official_identifier": "gss:E05000096",
        "slug": "northwick-park",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    }
  ]
}
"""
)  # noqa
current_elections_page_2 = json.loads(
    """
{
  "count": 518,
  "next": null,
  "previous": "https://elections.democracyclub.org.uk/api/elections/?limit=100&current=True",
  "results": [
    {
      "election_id": "local.brent.preston.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Brent local election Preston",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Brent",
        "common_name": "Brent",
        "gss": "E09000005",
        "slug": "brent",
        "territory_code": "ENG",
        "election_name": "Brent local election"
      },
      "group": "local.brent.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Preston",
        "official_identifier": "gss:E05000097",
        "slug": "preston",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.brent.queens-park.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Brent local election Queens Park",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Brent",
        "common_name": "Brent",
        "gss": "E09000005",
        "slug": "brent",
        "territory_code": "ENG",
        "election_name": "Brent local election"
      },
      "group": "local.brent.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Queens Park",
        "official_identifier": "gss:E05000098",
        "slug": "queens-park",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.brent.queensbury.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Brent local election Queensbury",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Brent",
        "common_name": "Brent",
        "gss": "E09000005",
        "slug": "brent",
        "territory_code": "ENG",
        "election_name": "Brent local election"
      },
      "group": "local.brent.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Queensbury",
        "official_identifier": "gss:E05000099",
        "slug": "queensbury",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.brent.stonebridge.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Brent local election Stonebridge",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Brent",
        "common_name": "Brent",
        "gss": "E09000005",
        "slug": "brent",
        "territory_code": "ENG",
        "election_name": "Brent local election"
      },
      "group": "local.brent.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Stonebridge",
        "official_identifier": "gss:E05000100",
        "slug": "stonebridge",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.brent.sudbury.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Brent local election Sudbury",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Brent",
        "common_name": "Brent",
        "gss": "E09000005",
        "slug": "brent",
        "territory_code": "ENG",
        "election_name": "Brent local election"
      },
      "group": "local.brent.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Sudbury",
        "official_identifier": "gss:E05000101",
        "slug": "sudbury",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.brent.tokyngton.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Brent local election Tokyngton",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Brent",
        "common_name": "Brent",
        "gss": "E09000005",
        "slug": "brent",
        "territory_code": "ENG",
        "election_name": "Brent local election"
      },
      "group": "local.brent.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Tokyngton",
        "official_identifier": "gss:E05000102",
        "slug": "tokyngton",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.brent.welsh-harp.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Brent local election Welsh Harp",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Brent",
        "common_name": "Brent",
        "gss": "E09000005",
        "slug": "brent",
        "territory_code": "ENG",
        "election_name": "Brent local election"
      },
      "group": "local.brent.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Welsh Harp",
        "official_identifier": "gss:E05000103",
        "slug": "welsh-harp",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.brent.wembley-central.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Brent local election Wembley Central",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Brent",
        "common_name": "Brent",
        "gss": "E09000005",
        "slug": "brent",
        "territory_code": "ENG",
        "election_name": "Brent local election"
      },
      "group": "local.brent.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Wembley Central",
        "official_identifier": "gss:E05000104",
        "slug": "wembley-central",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.brent.willesden-green.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Brent local election Willesden Green",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Brent",
        "common_name": "Brent",
        "gss": "E09000005",
        "slug": "brent",
        "territory_code": "ENG",
        "election_name": "Brent local election"
      },
      "group": "local.brent.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Willesden Green",
        "official_identifier": "gss:E05000105",
        "slug": "willesden-green",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bromley.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bromley local election",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BRY",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Bromley",
        "common_name": "Bromley",
        "gss": "E09000006",
        "slug": "bromley",
        "territory_code": "ENG",
        "election_name": "Bromley local election"
      },
      "group": "local.2018-02-22",
      "group_type": "organisation",
      "children": [
        "local.bromley.bickley.2018-02-22",
        "local.bromley.biggin-hill.2018-02-22",
        "local.bromley.bromley-common-and-keston.2018-02-22",
        "local.bromley.bromley-town.2018-02-22",
        "local.bromley.chelsfield-and-pratts-bottom.2018-02-22",
        "local.bromley.chislehurst.2018-02-22",
        "local.bromley.clock-house.2018-02-22",
        "local.bromley.copers-cope.2018-02-22",
        "local.bromley.cray-valley-east.2018-02-22",
        "local.bromley.cray-valley-west.2018-02-22",
        "local.bromley.crystal-palace.2018-02-22",
        "local.bromley.darwin.2018-02-22",
        "local.bromley.farnborough-and-crofton.2018-02-22",
        "local.bromley.hayes-and-coney-hall.2018-02-22",
        "local.bromley.kelsey-and-eden-park.2018-02-22",
        "local.bromley.mottingham-and-chislehurst-north.2018-02-22",
        "local.bromley.orpington.2018-02-22",
        "local.bromley.penge-and-cator.2018-02-22",
        "local.bromley.petts-wood-and-knoll.2018-02-22",
        "local.bromley.plaistow-and-sundridge.2018-02-22",
        "local.bromley.shortlands.2018-02-22",
        "local.bromley.west-wickham.2018-02-22"
      ],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": null,
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bromley.bickley.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bromley local election Bickley",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BRY",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Bromley",
        "common_name": "Bromley",
        "gss": "E09000006",
        "slug": "bromley",
        "territory_code": "ENG",
        "election_name": "Bromley local election"
      },
      "group": "local.bromley.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Bickley",
        "official_identifier": "gss:E05000106",
        "slug": "bickley",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bromley.biggin-hill.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bromley local election Biggin Hill",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BRY",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Bromley",
        "common_name": "Bromley",
        "gss": "E09000006",
        "slug": "bromley",
        "territory_code": "ENG",
        "election_name": "Bromley local election"
      },
      "group": "local.bromley.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Biggin Hill",
        "official_identifier": "gss:E05000107",
        "slug": "biggin-hill",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bromley.bromley-common-and-keston.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bromley local election Bromley Common and Keston",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BRY",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Bromley",
        "common_name": "Bromley",
        "gss": "E09000006",
        "slug": "bromley",
        "territory_code": "ENG",
        "election_name": "Bromley local election"
      },
      "group": "local.bromley.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Bromley Common and Keston",
        "official_identifier": "gss:E05000108",
        "slug": "bromley-common-and-keston",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bromley.bromley-town.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bromley local election Bromley Town",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BRY",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Bromley",
        "common_name": "Bromley",
        "gss": "E09000006",
        "slug": "bromley",
        "territory_code": "ENG",
        "election_name": "Bromley local election"
      },
      "group": "local.bromley.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Bromley Town",
        "official_identifier": "gss:E05000109",
        "slug": "bromley-town",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bromley.chelsfield-and-pratts-bottom.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bromley local election Chelsfield and Pratts Bottom",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BRY",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Bromley",
        "common_name": "Bromley",
        "gss": "E09000006",
        "slug": "bromley",
        "territory_code": "ENG",
        "election_name": "Bromley local election"
      },
      "group": "local.bromley.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Chelsfield and Pratts Bottom",
        "official_identifier": "gss:E05000110",
        "slug": "chelsfield-and-pratts-bottom",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bromley.chislehurst.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bromley local election Chislehurst",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BRY",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Bromley",
        "common_name": "Bromley",
        "gss": "E09000006",
        "slug": "bromley",
        "territory_code": "ENG",
        "election_name": "Bromley local election"
      },
      "group": "local.bromley.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Chislehurst",
        "official_identifier": "gss:E05000111",
        "slug": "chislehurst",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bromley.clock-house.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bromley local election Clock House",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BRY",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Bromley",
        "common_name": "Bromley",
        "gss": "E09000006",
        "slug": "bromley",
        "territory_code": "ENG",
        "election_name": "Bromley local election"
      },
      "group": "local.bromley.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Clock House",
        "official_identifier": "gss:E05000112",
        "slug": "clock-house",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bromley.copers-cope.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bromley local election Copers Cope",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BRY",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Bromley",
        "common_name": "Bromley",
        "gss": "E09000006",
        "slug": "bromley",
        "territory_code": "ENG",
        "election_name": "Bromley local election"
      },
      "group": "local.bromley.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Copers Cope",
        "official_identifier": "gss:E05000113",
        "slug": "copers-cope",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bromley.cray-valley-east.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bromley local election Cray Valley East",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BRY",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Bromley",
        "common_name": "Bromley",
        "gss": "E09000006",
        "slug": "bromley",
        "territory_code": "ENG",
        "election_name": "Bromley local election"
      },
      "group": "local.bromley.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Cray Valley East",
        "official_identifier": "gss:E05000114",
        "slug": "cray-valley-east",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bromley.cray-valley-west.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bromley local election Cray Valley West",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BRY",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Bromley",
        "common_name": "Bromley",
        "gss": "E09000006",
        "slug": "bromley",
        "territory_code": "ENG",
        "election_name": "Bromley local election"
      },
      "group": "local.bromley.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Cray Valley West",
        "official_identifier": "gss:E05000115",
        "slug": "cray-valley-west",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bromley.crystal-palace.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bromley local election Crystal Palace",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BRY",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Bromley",
        "common_name": "Bromley",
        "gss": "E09000006",
        "slug": "bromley",
        "territory_code": "ENG",
        "election_name": "Bromley local election"
      },
      "group": "local.bromley.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Crystal Palace",
        "official_identifier": "gss:E05000116",
        "slug": "crystal-palace",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bromley.darwin.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bromley local election Darwin",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BRY",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Bromley",
        "common_name": "Bromley",
        "gss": "E09000006",
        "slug": "bromley",
        "territory_code": "ENG",
        "election_name": "Bromley local election"
      },
      "group": "local.bromley.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Darwin",
        "official_identifier": "gss:E05000117",
        "slug": "darwin",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bromley.farnborough-and-crofton.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bromley local election Farnborough and Crofton",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BRY",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Bromley",
        "common_name": "Bromley",
        "gss": "E09000006",
        "slug": "bromley",
        "territory_code": "ENG",
        "election_name": "Bromley local election"
      },
      "group": "local.bromley.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Farnborough and Crofton",
        "official_identifier": "gss:E05000118",
        "slug": "farnborough-and-crofton",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bromley.hayes-and-coney-hall.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bromley local election Hayes and Coney Hall",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BRY",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Bromley",
        "common_name": "Bromley",
        "gss": "E09000006",
        "slug": "bromley",
        "territory_code": "ENG",
        "election_name": "Bromley local election"
      },
      "group": "local.bromley.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Hayes and Coney Hall",
        "official_identifier": "gss:E05000119",
        "slug": "hayes-and-coney-hall",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bromley.kelsey-and-eden-park.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bromley local election Kelsey and Eden Park",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BRY",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Bromley",
        "common_name": "Bromley",
        "gss": "E09000006",
        "slug": "bromley",
        "territory_code": "ENG",
        "election_name": "Bromley local election"
      },
      "group": "local.bromley.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Kelsey and Eden Park",
        "official_identifier": "gss:E05000120",
        "slug": "kelsey-and-eden-park",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bromley.mottingham-and-chislehurst-north.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bromley local election Mottingham and Chislehurst North",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BRY",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Bromley",
        "common_name": "Bromley",
        "gss": "E09000006",
        "slug": "bromley",
        "territory_code": "ENG",
        "election_name": "Bromley local election"
      },
      "group": "local.bromley.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Mottingham and Chislehurst North",
        "official_identifier": "gss:E05000121",
        "slug": "mottingham-and-chislehurst-north",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bromley.orpington.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bromley local election Orpington",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BRY",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Bromley",
        "common_name": "Bromley",
        "gss": "E09000006",
        "slug": "bromley",
        "territory_code": "ENG",
        "election_name": "Bromley local election"
      },
      "group": "local.bromley.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Orpington",
        "official_identifier": "gss:E05000122",
        "slug": "orpington",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bromley.penge-and-cator.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bromley local election Penge and Cator",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BRY",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Bromley",
        "common_name": "Bromley",
        "gss": "E09000006",
        "slug": "bromley",
        "territory_code": "ENG",
        "election_name": "Bromley local election"
      },
      "group": "local.bromley.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Penge and Cator",
        "official_identifier": "gss:E05000123",
        "slug": "penge-and-cator",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bromley.petts-wood-and-knoll.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bromley local election Petts Wood and Knoll",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BRY",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Bromley",
        "common_name": "Bromley",
        "gss": "E09000006",
        "slug": "bromley",
        "territory_code": "ENG",
        "election_name": "Bromley local election"
      },
      "group": "local.bromley.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Petts Wood and Knoll",
        "official_identifier": "gss:E05000124",
        "slug": "petts-wood-and-knoll",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bromley.plaistow-and-sundridge.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bromley local election Plaistow and Sundridge",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BRY",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Bromley",
        "common_name": "Bromley",
        "gss": "E09000006",
        "slug": "bromley",
        "territory_code": "ENG",
        "election_name": "Bromley local election"
      },
      "group": "local.bromley.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Plaistow and Sundridge",
        "official_identifier": "gss:E05000125",
        "slug": "plaistow-and-sundridge",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bromley.shortlands.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bromley local election Shortlands",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BRY",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Bromley",
        "common_name": "Bromley",
        "gss": "E09000006",
        "slug": "bromley",
        "territory_code": "ENG",
        "election_name": "Bromley local election"
      },
      "group": "local.bromley.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Shortlands",
        "official_identifier": "gss:E05000126",
        "slug": "shortlands",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.bromley.west-wickham.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Bromley local election West Wickham",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "BRY",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Bromley",
        "common_name": "Bromley",
        "gss": "E09000006",
        "slug": "bromley",
        "territory_code": "ENG",
        "election_name": "Bromley local election"
      },
      "group": "local.bromley.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "West Wickham",
        "official_identifier": "gss:E05000127",
        "slug": "west-wickham",
        "division_type": "LBW",
        "division_subtype": "London borough ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.daventry.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Daventry local election",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DAV",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Daventry District Council",
        "common_name": "Daventry",
        "gss": "E07000151",
        "slug": "daventry",
        "territory_code": "ENG",
        "election_name": "Daventry local election"
      },
      "group": "local.2018-02-22",
      "group_type": "organisation",
      "children": [
        "local.daventry.abbey-north.2018-02-22",
        "local.daventry.abbey-south.2018-02-22",
        "local.daventry.barby-and-kilsby.2018-02-22",
        "local.daventry.braunston-and-welton.2018-02-22",
        "local.daventry.brixworth.2018-02-22",
        "local.daventry.drayton.2018-02-22",
        "local.daventry.hill.2018-02-22",
        "local.daventry.long-buckby.2018-02-22",
        "local.daventry.moulton.2018-02-22",
        "local.daventry.ravensthorpe.2018-02-22",
        "local.daventry.spratton.2018-02-22",
        "local.daventry.walgrave.2018-02-22",
        "local.daventry.weedon.2018-02-22",
        "local.daventry.welford.2018-02-22",
        "local.daventry.woodford.2018-02-22",
        "local.daventry.yelvertoft.2018-02-22"
      ],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": null,
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.daventry.abbey-north.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Daventry local election Abbey North",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DAV",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Daventry District Council",
        "common_name": "Daventry",
        "gss": "E07000151",
        "slug": "daventry",
        "territory_code": "ENG",
        "election_name": "Daventry local election"
      },
      "group": "local.daventry.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2012-05-31",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2012 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Abbey North",
        "official_identifier": "gss:E05009012",
        "slug": "abbey-north",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.daventry.abbey-south.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Daventry local election Abbey South",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DAV",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Daventry District Council",
        "common_name": "Daventry",
        "gss": "E07000151",
        "slug": "daventry",
        "territory_code": "ENG",
        "election_name": "Daventry local election"
      },
      "group": "local.daventry.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2012-05-31",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2012 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Abbey South",
        "official_identifier": "gss:E05009013",
        "slug": "abbey-south",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.daventry.barby-and-kilsby.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Daventry local election Barby and Kilsby",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DAV",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Daventry District Council",
        "common_name": "Daventry",
        "gss": "E07000151",
        "slug": "daventry",
        "territory_code": "ENG",
        "election_name": "Daventry local election"
      },
      "group": "local.daventry.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2012-05-31",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2012 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Barby and Kilsby",
        "official_identifier": "gss:E05009014",
        "slug": "barby-and-kilsby",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.daventry.braunston-and-welton.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Daventry local election Braunston and Welton",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DAV",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Daventry District Council",
        "common_name": "Daventry",
        "gss": "E07000151",
        "slug": "daventry",
        "territory_code": "ENG",
        "election_name": "Daventry local election"
      },
      "group": "local.daventry.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2012-05-31",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2012 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Braunston and Welton",
        "official_identifier": "gss:E05009015",
        "slug": "braunston-and-welton",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.daventry.brixworth.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Daventry local election Brixworth",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DAV",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Daventry District Council",
        "common_name": "Daventry",
        "gss": "E07000151",
        "slug": "daventry",
        "territory_code": "ENG",
        "election_name": "Daventry local election"
      },
      "group": "local.daventry.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2012-05-31",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2012 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Brixworth",
        "official_identifier": "gss:E05009016",
        "slug": "brixworth",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.daventry.drayton.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Daventry local election Drayton",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DAV",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Daventry District Council",
        "common_name": "Daventry",
        "gss": "E07000151",
        "slug": "daventry",
        "territory_code": "ENG",
        "election_name": "Daventry local election"
      },
      "group": "local.daventry.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2012-05-31",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2012 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Drayton",
        "official_identifier": "gss:E05009017",
        "slug": "drayton",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.daventry.hill.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Daventry local election Hill",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DAV",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Daventry District Council",
        "common_name": "Daventry",
        "gss": "E07000151",
        "slug": "daventry",
        "territory_code": "ENG",
        "election_name": "Daventry local election"
      },
      "group": "local.daventry.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2012-05-31",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2012 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Hill",
        "official_identifier": "gss:E05009018",
        "slug": "hill",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.daventry.long-buckby.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Daventry local election Long Buckby",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DAV",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Daventry District Council",
        "common_name": "Daventry",
        "gss": "E07000151",
        "slug": "daventry",
        "territory_code": "ENG",
        "election_name": "Daventry local election"
      },
      "group": "local.daventry.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2012-05-31",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2012 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Long Buckby",
        "official_identifier": "gss:E05009019",
        "slug": "long-buckby",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.daventry.moulton.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Daventry local election Moulton",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DAV",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Daventry District Council",
        "common_name": "Daventry",
        "gss": "E07000151",
        "slug": "daventry",
        "territory_code": "ENG",
        "election_name": "Daventry local election"
      },
      "group": "local.daventry.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2012-05-31",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2012 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Moulton",
        "official_identifier": "gss:E05009020",
        "slug": "moulton",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.daventry.ravensthorpe.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Daventry local election Ravensthorpe",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DAV",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Daventry District Council",
        "common_name": "Daventry",
        "gss": "E07000151",
        "slug": "daventry",
        "territory_code": "ENG",
        "election_name": "Daventry local election"
      },
      "group": "local.daventry.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2012-05-31",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2012 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Ravensthorpe",
        "official_identifier": "gss:E05009021",
        "slug": "ravensthorpe",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.daventry.spratton.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Daventry local election Spratton",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DAV",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Daventry District Council",
        "common_name": "Daventry",
        "gss": "E07000151",
        "slug": "daventry",
        "territory_code": "ENG",
        "election_name": "Daventry local election"
      },
      "group": "local.daventry.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2012-05-31",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2012 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Spratton",
        "official_identifier": "gss:E05009022",
        "slug": "spratton",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.daventry.walgrave.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Daventry local election Walgrave",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DAV",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Daventry District Council",
        "common_name": "Daventry",
        "gss": "E07000151",
        "slug": "daventry",
        "territory_code": "ENG",
        "election_name": "Daventry local election"
      },
      "group": "local.daventry.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2012-05-31",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2012 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Walgrave",
        "official_identifier": "gss:E05009023",
        "slug": "walgrave",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.daventry.weedon.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Daventry local election Weedon",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DAV",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Daventry District Council",
        "common_name": "Daventry",
        "gss": "E07000151",
        "slug": "daventry",
        "territory_code": "ENG",
        "election_name": "Daventry local election"
      },
      "group": "local.daventry.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2012-05-31",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2012 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Weedon",
        "official_identifier": "gss:E05009024",
        "slug": "weedon",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.daventry.welford.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Daventry local election Welford",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DAV",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Daventry District Council",
        "common_name": "Daventry",
        "gss": "E07000151",
        "slug": "daventry",
        "territory_code": "ENG",
        "election_name": "Daventry local election"
      },
      "group": "local.daventry.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2012-05-31",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2012 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Welford",
        "official_identifier": "gss:E05009025",
        "slug": "welford",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.daventry.woodford.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Daventry local election Woodford",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DAV",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Daventry District Council",
        "common_name": "Daventry",
        "gss": "E07000151",
        "slug": "daventry",
        "territory_code": "ENG",
        "election_name": "Daventry local election"
      },
      "group": "local.daventry.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2012-05-31",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2012 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Woodford",
        "official_identifier": "gss:E05009026",
        "slug": "woodford",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.daventry.yelvertoft.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Daventry local election Yelvertoft",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DAV",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Daventry District Council",
        "common_name": "Daventry",
        "gss": "E07000151",
        "slug": "daventry",
        "territory_code": "ENG",
        "election_name": "Daventry local election"
      },
      "group": "local.daventry.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2012-05-31",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2012 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Yelvertoft",
        "official_identifier": "gss:E05009027",
        "slug": "yelvertoft",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.2018-02-22",
      "group_type": "organisation",
      "children": [
        "local.denbighshire.bodelwyddan.2018-02-22",
        "local.denbighshire.corwen.2018-02-22",
        "local.denbighshire.denbigh-central.2018-02-22",
        "local.denbighshire.denbigh-lower.2018-02-22",
        "local.denbighshire.denbigh-upperhenllan.2018-02-22",
        "local.denbighshire.dyserth.2018-02-22",
        "local.denbighshire.efenechtyd.2018-02-22",
        "local.denbighshire.llanarmon-yn-ialllandegla.2018-02-22",
        "local.denbighshire.llanbedr-dyffryn-clwydllangynhafal.2018-02-22",
        "local.denbighshire.llandrillo.2018-02-22",
        "local.denbighshire.llandyrnog.2018-02-22",
        "local.denbighshire.llanfair-dyffryn-clwydgwyddelwern.2018-02-22",
        "local.denbighshire.llangollen.2018-02-22",
        "local.denbighshire.llanrhaeadr-yng-nghinmeirch.2018-02-22",
        "local.denbighshire.prestatyn-central.2018-02-22",
        "local.denbighshire.prestatyn-east.2018-02-22",
        "local.denbighshire.prestatyn-meliden.2018-02-22",
        "local.denbighshire.prestatyn-north.2018-02-22",
        "local.denbighshire.prestatyn-south-west.2018-02-22",
        "local.denbighshire.rhuddlan.2018-02-22",
        "local.denbighshire.rhyl-east.2018-02-22",
        "local.denbighshire.rhyl-south-east.2018-02-22",
        "local.denbighshire.rhyl-south-west.2018-02-22",
        "local.denbighshire.rhyl-south.2018-02-22",
        "local.denbighshire.rhyl-west.2018-02-22",
        "local.denbighshire.ruthin.2018-02-22",
        "local.denbighshire.st-asaph-east.2018-02-22",
        "local.denbighshire.st-asaph-west.2018-02-22",
        "local.denbighshire.trefnant.2018-02-22",
        "local.denbighshire.tremeirchion.2018-02-22"
      ],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": null,
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.bodelwyddan.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Bodelwyddan",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Bodelwyddan",
        "official_identifier": "gss:W05000150",
        "slug": "bodelwyddan",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.corwen.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Corwen",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Corwen",
        "official_identifier": "gss:W05000151",
        "slug": "corwen",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.denbigh-central.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Denbigh Central",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Denbigh Central",
        "official_identifier": "gss:W05000152",
        "slug": "denbigh-central",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.denbigh-lower.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Denbigh Lower",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Denbigh Lower",
        "official_identifier": "gss:W05000153",
        "slug": "denbigh-lower",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.denbigh-upperhenllan.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Denbigh Upper/Henllan",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Denbigh Upper/Henllan",
        "official_identifier": "gss:W05000154",
        "slug": "denbigh-upperhenllan",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.dyserth.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Dyserth",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Dyserth",
        "official_identifier": "gss:W05000155",
        "slug": "dyserth",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.efenechtyd.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Efenechtyd",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Efenechtyd",
        "official_identifier": "gss:W05000156",
        "slug": "efenechtyd",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.llanarmon-yn-ialllandegla.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Llanarmon-yn-Ial/Llandegla",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Llanarmon-yn-Ial/Llandegla",
        "official_identifier": "gss:W05000157",
        "slug": "llanarmon-yn-ialllandegla",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.llanbedr-dyffryn-clwydllangynhafal.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Llanbedr Dyffryn Clwyd/Llangynhafal",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Llanbedr Dyffryn Clwyd/Llangynhafal",
        "official_identifier": "gss:W05000158",
        "slug": "llanbedr-dyffryn-clwydllangynhafal",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.llandrillo.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Llandrillo",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Llandrillo",
        "official_identifier": "gss:W05000159",
        "slug": "llandrillo",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.llandyrnog.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Llandyrnog",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Llandyrnog",
        "official_identifier": "gss:W05000160",
        "slug": "llandyrnog",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.llanfair-dyffryn-clwydgwyddelwern.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Llanfair Dyffryn Clwyd/Gwyddelwern",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Llanfair Dyffryn Clwyd/Gwyddelwern",
        "official_identifier": "gss:W05000161",
        "slug": "llanfair-dyffryn-clwydgwyddelwern",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.llangollen.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Llangollen",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Llangollen",
        "official_identifier": "gss:W05000162",
        "slug": "llangollen",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.llanrhaeadr-yng-nghinmeirch.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Llanrhaeadr-Yng-Nghinmeirch",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Llanrhaeadr-Yng-Nghinmeirch",
        "official_identifier": "gss:W05000163",
        "slug": "llanrhaeadr-yng-nghinmeirch",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.prestatyn-central.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Prestatyn Central",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Prestatyn Central",
        "official_identifier": "gss:W05000164",
        "slug": "prestatyn-central",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.prestatyn-east.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Prestatyn East",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Prestatyn East",
        "official_identifier": "gss:W05000165",
        "slug": "prestatyn-east",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.prestatyn-meliden.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Prestatyn Meliden",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Prestatyn Meliden",
        "official_identifier": "gss:W05000166",
        "slug": "prestatyn-meliden",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.prestatyn-north.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Prestatyn North",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Prestatyn North",
        "official_identifier": "gss:W05000167",
        "slug": "prestatyn-north",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.prestatyn-south-west.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Prestatyn South West",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Prestatyn South West",
        "official_identifier": "gss:W05000168",
        "slug": "prestatyn-south-west",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.rhuddlan.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Rhuddlan",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Rhuddlan",
        "official_identifier": "gss:W05000169",
        "slug": "rhuddlan",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.rhyl-east.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Rhyl East",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Rhyl East",
        "official_identifier": "gss:W05000170",
        "slug": "rhyl-east",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.rhyl-south-east.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Rhyl South East",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Rhyl South East",
        "official_identifier": "gss:W05000172",
        "slug": "rhyl-south-east",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.rhyl-south-west.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Rhyl South West",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Rhyl South West",
        "official_identifier": "gss:W05000173",
        "slug": "rhyl-south-west",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.rhyl-south.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Rhyl South",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Rhyl South",
        "official_identifier": "gss:W05000171",
        "slug": "rhyl-south",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.rhyl-west.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Rhyl West",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Rhyl West",
        "official_identifier": "gss:W05000174",
        "slug": "rhyl-west",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.ruthin.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Ruthin",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Ruthin",
        "official_identifier": "gss:W05000175",
        "slug": "ruthin",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.st-asaph-east.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election St Asaph East",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "St Asaph East",
        "official_identifier": "gss:W05000176",
        "slug": "st-asaph-east",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.st-asaph-west.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election St Asaph West",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "St Asaph West",
        "official_identifier": "gss:W05000177",
        "slug": "st-asaph-west",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.trefnant.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Trefnant",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Trefnant",
        "official_identifier": "gss:W05000178",
        "slug": "trefnant",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.denbighshire.tremeirchion.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Denbighshire local election Tremeirchion",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "DEN",
        "organisation_type": "local-authority",
        "organisation_subtype": "UA",
        "official_name": "Denbighshire County Council",
        "common_name": "Denbighshire",
        "gss": "W06000004",
        "slug": "denbighshire",
        "territory_code": "WLS",
        "election_name": "Denbighshire local election"
      },
      "group": "local.denbighshire.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Tremeirchion",
        "official_identifier": "gss:W05000179",
        "slug": "tremeirchion",
        "division_type": "UTE",
        "division_subtype": "Unitary Authority electoral division (UTE)",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.eden.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Eden local election",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "EDN",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Eden District Council",
        "common_name": "Eden",
        "gss": "E07000030",
        "slug": "eden",
        "territory_code": "ENG",
        "election_name": "Eden local election"
      },
      "group": "local.2018-02-22",
      "group_type": "organisation",
      "children": [
        "local.eden.alston-moor.2018-02-22",
        "local.eden.appleby-appleby.2018-02-22",
        "local.eden.appleby-bongate.2018-02-22",
        "local.eden.askham.2018-02-22",
        "local.eden.brough.2018-02-22",
        "local.eden.crosby-ravensworth.2018-02-22",
        "local.eden.dacre.2018-02-22",
        "local.eden.eamont.2018-02-22",
        "local.eden.greystoke.2018-02-22",
        "local.eden.hartside.2018-02-22",
        "local.eden.hesket.2018-02-22",
        "local.eden.kirkby-stephen.2018-02-22",
        "local.eden.kirkby-thore.2018-02-22",
        "local.eden.kirkoswald.2018-02-22",
        "local.eden.langwathby.2018-02-22",
        "local.eden.lazonby.2018-02-22",
        "local.eden.long-marton.2018-02-22",
        "local.eden.morland.2018-02-22",
        "local.eden.orton-with-tebay.2018-02-22",
        "local.eden.penrith-carleton.2018-02-22",
        "local.eden.penrith-east.2018-02-22",
        "local.eden.penrith-north.2018-02-22",
        "local.eden.penrith-pategill.2018-02-22",
        "local.eden.penrith-south.2018-02-22",
        "local.eden.penrith-west.2018-02-22",
        "local.eden.ravenstonedale.2018-02-22",
        "local.eden.shap.2018-02-22",
        "local.eden.skelton.2018-02-22",
        "local.eden.ullswater.2018-02-22",
        "local.eden.warcop.2018-02-22"
      ],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": null,
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.eden.alston-moor.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Eden local election Alston Moor",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "EDN",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Eden District Council",
        "common_name": "Eden",
        "gss": "E07000030",
        "slug": "eden",
        "territory_code": "ENG",
        "election_name": "Eden local election"
      },
      "group": "local.eden.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Alston Moor",
        "official_identifier": "gss:E05003205",
        "slug": "alston-moor",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.eden.appleby-appleby.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Eden local election Appleby (Appleby)",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "EDN",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Eden District Council",
        "common_name": "Eden",
        "gss": "E07000030",
        "slug": "eden",
        "territory_code": "ENG",
        "election_name": "Eden local election"
      },
      "group": "local.eden.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Appleby (Appleby)",
        "official_identifier": "gss:E05003206",
        "slug": "appleby-appleby",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.eden.appleby-bongate.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Eden local election Appleby (Bongate)",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "EDN",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Eden District Council",
        "common_name": "Eden",
        "gss": "E07000030",
        "slug": "eden",
        "territory_code": "ENG",
        "election_name": "Eden local election"
      },
      "group": "local.eden.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Appleby (Bongate)",
        "official_identifier": "gss:E05003207",
        "slug": "appleby-bongate",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.eden.askham.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Eden local election Askham",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "EDN",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Eden District Council",
        "common_name": "Eden",
        "gss": "E07000030",
        "slug": "eden",
        "territory_code": "ENG",
        "election_name": "Eden local election"
      },
      "group": "local.eden.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Askham",
        "official_identifier": "gss:E05003208",
        "slug": "askham",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.eden.brough.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Eden local election Brough",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "EDN",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Eden District Council",
        "common_name": "Eden",
        "gss": "E07000030",
        "slug": "eden",
        "territory_code": "ENG",
        "election_name": "Eden local election"
      },
      "group": "local.eden.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Brough",
        "official_identifier": "gss:E05003209",
        "slug": "brough",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.eden.crosby-ravensworth.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Eden local election Crosby Ravensworth",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "EDN",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Eden District Council",
        "common_name": "Eden",
        "gss": "E07000030",
        "slug": "eden",
        "territory_code": "ENG",
        "election_name": "Eden local election"
      },
      "group": "local.eden.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Crosby Ravensworth",
        "official_identifier": "gss:E05003210",
        "slug": "crosby-ravensworth",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.eden.dacre.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Eden local election Dacre",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "EDN",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Eden District Council",
        "common_name": "Eden",
        "gss": "E07000030",
        "slug": "eden",
        "territory_code": "ENG",
        "election_name": "Eden local election"
      },
      "group": "local.eden.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Dacre",
        "official_identifier": "gss:E05003211",
        "slug": "dacre",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.eden.eamont.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Eden local election Eamont",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "EDN",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Eden District Council",
        "common_name": "Eden",
        "gss": "E07000030",
        "slug": "eden",
        "territory_code": "ENG",
        "election_name": "Eden local election"
      },
      "group": "local.eden.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Eamont",
        "official_identifier": "gss:E05003212",
        "slug": "eamont",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.eden.greystoke.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Eden local election Greystoke",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "EDN",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Eden District Council",
        "common_name": "Eden",
        "gss": "E07000030",
        "slug": "eden",
        "territory_code": "ENG",
        "election_name": "Eden local election"
      },
      "group": "local.eden.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Greystoke",
        "official_identifier": "gss:E05003213",
        "slug": "greystoke",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.eden.hartside.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Eden local election Hartside",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "EDN",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Eden District Council",
        "common_name": "Eden",
        "gss": "E07000030",
        "slug": "eden",
        "territory_code": "ENG",
        "election_name": "Eden local election"
      },
      "group": "local.eden.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Hartside",
        "official_identifier": "gss:E05003214",
        "slug": "hartside",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.eden.hesket.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Eden local election Hesket",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "EDN",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Eden District Council",
        "common_name": "Eden",
        "gss": "E07000030",
        "slug": "eden",
        "territory_code": "ENG",
        "election_name": "Eden local election"
      },
      "group": "local.eden.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Hesket",
        "official_identifier": "gss:E05003215",
        "slug": "hesket",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.eden.kirkby-stephen.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Eden local election Kirkby Stephen",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "EDN",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Eden District Council",
        "common_name": "Eden",
        "gss": "E07000030",
        "slug": "eden",
        "territory_code": "ENG",
        "election_name": "Eden local election"
      },
      "group": "local.eden.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Kirkby Stephen",
        "official_identifier": "gss:E05003216",
        "slug": "kirkby-stephen",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.eden.kirkby-thore.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Eden local election Kirkby Thore",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "EDN",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Eden District Council",
        "common_name": "Eden",
        "gss": "E07000030",
        "slug": "eden",
        "territory_code": "ENG",
        "election_name": "Eden local election"
      },
      "group": "local.eden.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Kirkby Thore",
        "official_identifier": "gss:E05003217",
        "slug": "kirkby-thore",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.eden.kirkoswald.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Eden local election Kirkoswald",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "EDN",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Eden District Council",
        "common_name": "Eden",
        "gss": "E07000030",
        "slug": "eden",
        "territory_code": "ENG",
        "election_name": "Eden local election"
      },
      "group": "local.eden.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Kirkoswald",
        "official_identifier": "gss:E05003218",
        "slug": "kirkoswald",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.eden.langwathby.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Eden local election Langwathby",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "EDN",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Eden District Council",
        "common_name": "Eden",
        "gss": "E07000030",
        "slug": "eden",
        "territory_code": "ENG",
        "election_name": "Eden local election"
      },
      "group": "local.eden.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Langwathby",
        "official_identifier": "gss:E05003219",
        "slug": "langwathby",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.eden.lazonby.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Eden local election Lazonby",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "EDN",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Eden District Council",
        "common_name": "Eden",
        "gss": "E07000030",
        "slug": "eden",
        "territory_code": "ENG",
        "election_name": "Eden local election"
      },
      "group": "local.eden.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Lazonby",
        "official_identifier": "gss:E05003220",
        "slug": "lazonby",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.eden.long-marton.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Eden local election Long Marton",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "EDN",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Eden District Council",
        "common_name": "Eden",
        "gss": "E07000030",
        "slug": "eden",
        "territory_code": "ENG",
        "election_name": "Eden local election"
      },
      "group": "local.eden.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Long Marton",
        "official_identifier": "gss:E05003221",
        "slug": "long-marton",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.eden.morland.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Eden local election Morland",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "EDN",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Eden District Council",
        "common_name": "Eden",
        "gss": "E07000030",
        "slug": "eden",
        "territory_code": "ENG",
        "election_name": "Eden local election"
      },
      "group": "local.eden.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Morland",
        "official_identifier": "gss:E05003222",
        "slug": "morland",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.eden.orton-with-tebay.2018-02-22",
      "tmp_election_id": null,
      "election_title": "Eden local election Orton with Tebay",
      "poll_open_date": "2018-02-22",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "EDN",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Eden District Council",
        "common_name": "Eden",
        "gss": "E07000030",
        "slug": "eden",
        "territory_code": "ENG",
        "election_name": "Eden local election"
      },
      "group": "local.eden.2018-02-22",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Orton with Tebay",
        "official_identifier": "gss:E05003223",
        "slug": "orton-with-tebay",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    }
  ]
}
"""
)  # noqa

each_type_of_election_on_one_day_parents = json.loads(
    """{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "election_id": "local.2019-01-17",
      "tmp_election_id": null,
      "election_title": "Local elections",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": null,
      "group": null,
      "group_type": "election",
      "children": [
        "local.adur.2019-01-17"
      ],
      "elected_role": null,
      "seats_contested": null,
      "division": null,
      "voting_system": null,
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "mayor.2019-01-17",
      "tmp_election_id": null,
      "election_title": "Greater Manchester",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Directly elected Mayor",
        "election_type": "mayor"
      },
      "election_subtype": null,
      "organisation": null,
      "group": null,
      "group_type": "election",
      "children": [
        "mayor.greater-manchester-ca.2019-01-17",
        "mayor.hackney.2019-01-17"
      ],
      "elected_role": "Mayor",
      "seats_contested": null,
      "division": null,
      "voting_system": null,
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "naw.2019-01-17",
      "tmp_election_id": null,
      "election_title": "",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Welsh assembly",
        "election_type": "naw"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "naw",
        "organisation_type": "naw",
        "organisation_subtype": "",
        "official_name": "Welsh assembly",
        "common_name": "Welsh assembly",
        "gss": "W08000001",
        "slug": "naw",
        "territory_code": "WLS",
        "election_name": "National Assembly for Wales election",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": null,
      "group_type": "election",
      "children": [
        "naw.c.2019-01-17",
        "naw.r.2019-01-17"
      ],
      "elected_role": "Assembly Member",
      "seats_contested": null,
      "division": null,
      "voting_system": null,
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "nia.2019-01-17",
      "tmp_election_id": null,
      "election_title": "",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Northern Ireland assembly",
        "election_type": "nia"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "nia",
        "organisation_type": "nia",
        "organisation_subtype": "",
        "official_name": "Northern Ireland assembly",
        "common_name": "Northern Ireland assembly",
        "gss": "N07000001",
        "slug": "nia",
        "territory_code": "NIR",
        "election_name": "Northern Ireland assembly election",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": null,
      "group_type": "election",
      "children": [
        "nia.lagan-valley.2019-01-17"
      ],
      "elected_role": "Assembly Member",
      "seats_contested": null,
      "division": null,
      "voting_system": null,
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "parl.2019-01-17",
      "tmp_election_id": null,
      "election_title": "",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "UK Parliament",
        "election_type": "parl"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "parl-hoc",
        "organisation_type": "parl",
        "organisation_subtype": "",
        "official_name": "House of Commons of the United Kingdom",
        "common_name": "House of Commons",
        "gss": "",
        "slug": "parl",
        "territory_code": "GBN",
        "election_name": "UK general election",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": null,
      "group_type": "election",
      "children": [
        "parl.aberavon.2019-01-17",
        "parl.ynys-mon.2019-01-17"
      ],
      "elected_role": "Member of Parliament",
      "seats_contested": null,
      "division": null,
      "voting_system": null,
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "pcc.2019-01-17",
      "tmp_election_id": null,
      "election_title": "Police and Crime Commissioner for Avon and Somerset Constabulary",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Police and crime commissioner",
        "election_type": "pcc"
      },
      "election_subtype": null,
      "organisation": null,
      "group": null,
      "group_type": "election",
      "children": [
        "pcc.avon-and-somerset.2019-01-17"
      ],
      "elected_role": "Police and Crime Commissioner",
      "seats_contested": null,
      "division": null,
      "voting_system": null,
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "sp.2019-01-17",
      "tmp_election_id": null,
      "election_title": "",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Scottish parliament",
        "election_type": "sp"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "sp",
        "organisation_type": "sp",
        "organisation_subtype": "",
        "official_name": "Scottish Parliament",
        "common_name": "Scottish Parliament",
        "gss": "S15000001",
        "slug": "sp",
        "territory_code": "SCT",
        "election_name": "Scottish parliament election",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": null,
      "group_type": "election",
      "children": [
        "sp.c.2019-01-17",
        "sp.r.2019-01-17"
      ],
      "elected_role": "Member of the Scottish Parliament",
      "seats_contested": null,
      "division": null,
      "voting_system": null,
      "current": true,
      "explanation": null,
      "cancelled": false
    }
  ]
}
    """
)
each_type_of_election_on_one_day = json.loads(
    """
{
  "count": 27,
  "next": null,
  "previous": null,
  "results": [
    {
      "election_id": "local.2019-01-17",
      "tmp_election_id": null,
      "election_title": "Adur local election",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ADU",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Adur District Council",
        "common_name": "Adur",
        "gss": "E07000223",
        "slug": "adur",
        "territory_code": "ENG",
        "election_name": "Adur local election"
      },
      "group": null,
      "group_type": "election",
      "children": [
        "local.adur.2019-01-17"
      ],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": null,
      "voting_system": null,
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.adur.2019-01-17",
      "tmp_election_id": null,
      "election_title": "Adur local election",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ADU",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Adur District Council",
        "common_name": "Adur",
        "gss": "E07000223",
        "slug": "adur",
        "territory_code": "ENG",
        "election_name": "Adur local election"
      },
      "group": "local.2019-01-17",
      "group_type": "organisation",
      "children": [
        "local.adur.buckingham.2019-01-17"
      ],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": null,
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "local.adur.buckingham.2019-01-17",
      "tmp_election_id": null,
      "election_title": "Adur local election Buckingham",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "ADU",
        "organisation_type": "local-authority",
        "organisation_subtype": "NMD",
        "official_name": "Adur District Council",
        "common_name": "Adur",
        "gss": "E07000223",
        "slug": "adur",
        "territory_code": "ENG",
        "election_name": "Adur local election"
      },
      "group": "local.adur.2019-01-17",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": 3,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Buckingham",
        "official_identifier": "gss:E05007562",
        "slug": "buckingham",
        "division_type": "DIW",
        "division_subtype": "District council ward",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "ENG"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "mayor.2019-01-17",
      "tmp_election_id": null,
      "election_title": "Greater Manchester",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Directly elected Mayor",
        "election_type": "mayor"
      },
      "election_subtype": null,
      "organisation": null,
      "group": null,
      "group_type": "election",
      "children": [
        "mayor.greater-manchester-ca.2019-01-17",
        "mayor.hackney.2019-01-17"
      ],
      "elected_role": "Mayor",
      "seats_contested": null,
      "division": null,
      "voting_system": null,
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "mayor.greater-manchester-ca.2019-01-17",
      "tmp_election_id": null,
      "election_title": "Greater Manchester",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Directly elected Mayor",
        "election_type": "mayor"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "greater-manchester-ca",
        "organisation_type": "combined-authority",
        "organisation_subtype": "",
        "official_name": "Greater Manchester",
        "common_name": "Greater Manchester",
        "gss": "",
        "slug": "greater-manchester-ca",
        "territory_code": "ENG",
        "election_name": "Greater Manchester",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": "mayor.2019-01-17",
      "group_type": null,
      "children": [],
      "elected_role": "Mayor",
      "seats_contested": null,
      "division": null,
      "voting_system": {
        "slug": "sv",
        "name": "Supplementary Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "mayor.hackney.2019-01-17",
      "tmp_election_id": null,
      "election_title": "Hackney local election",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Directly elected Mayor",
        "election_type": "mayor"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "HCK",
        "organisation_type": "local-authority",
        "organisation_subtype": "LBO",
        "official_name": "London Borough of Hackney",
        "common_name": "Hackney",
        "gss": "E09000012",
        "slug": "hackney",
        "territory_code": "ENG",
        "election_name": "Hackney local election",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": "mayor.2019-01-17",
      "group_type": "organisation",
      "children": [],
      "elected_role": "Mayor",
      "seats_contested": null,
      "division": null,
      "voting_system": {
        "slug": "sv",
        "name": "Supplementary Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "naw.2019-01-17",
      "tmp_election_id": null,
      "election_title": "",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Welsh assembly",
        "election_type": "naw"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "naw",
        "organisation_type": "naw",
        "organisation_subtype": "",
        "official_name": "Welsh assembly",
        "common_name": "Welsh assembly",
        "gss": "W08000001",
        "slug": "naw",
        "territory_code": "WLS",
        "election_name": "National Assembly for Wales election",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": null,
      "group_type": "election",
      "children": [
        "naw.c.2019-01-17",
        "naw.r.2019-01-17"
      ],
      "elected_role": "Assembly Member",
      "seats_contested": null,
      "division": null,
      "voting_system": null,
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "naw.c.2019-01-17",
      "tmp_election_id": null,
      "election_title": "(Constituencies)",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Welsh assembly",
        "election_type": "naw"
      },
      "election_subtype": {
        "name": "Constituencies",
        "election_subtype": "c"
      },
      "organisation": {
        "official_identifier": "naw",
        "organisation_type": "naw",
        "organisation_subtype": "",
        "official_name": "Welsh assembly",
        "common_name": "Welsh assembly",
        "gss": "W08000001",
        "slug": "naw",
        "territory_code": "WLS",
        "election_name": "National Assembly for Wales election",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": "naw.2019-01-17",
      "group_type": "subtype",
      "children": [
        "naw.c.aberavon.2019-01-17",
        "naw.c.mid-and-west-wales.2019-01-17"
      ],
      "elected_role": "Assembly Member",
      "seats_contested": null,
      "division": null,
      "voting_system": {
        "slug": "AMS",
        "name": "Additional Member System",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "naw.c.aberavon.2019-01-17",
      "tmp_election_id": null,
      "election_title": "Aberavon (Constituencies)",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Welsh assembly",
        "election_type": "naw"
      },
      "election_subtype": {
        "name": "Constituencies",
        "election_subtype": "c"
      },
      "organisation": {
        "official_identifier": "naw",
        "organisation_type": "naw",
        "organisation_subtype": "",
        "official_name": "Welsh assembly",
        "common_name": "Welsh assembly",
        "gss": "W08000001",
        "slug": "naw",
        "territory_code": "WLS",
        "election_name": "National Assembly for Wales election",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": "naw.c.2019-01-17",
      "group_type": null,
      "children": [],
      "elected_role": "Assembly Member",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2016-04-13",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2016 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Aberavon",
        "official_identifier": "gss:W09000022",
        "slug": "aberavon",
        "division_type": "WAC",
        "division_subtype": "Welsh Assembly constituency",
        "division_election_sub_type": "c",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "AMS",
        "name": "Additional Member System",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "naw.c.mid-and-west-wales.2019-01-17",
      "tmp_election_id": null,
      "election_title": "Mid and West Wales (Constituencies)",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Welsh assembly",
        "election_type": "naw"
      },
      "election_subtype": {
        "name": "Constituencies",
        "election_subtype": "c"
      },
      "organisation": {
        "official_identifier": "naw",
        "organisation_type": "naw",
        "organisation_subtype": "",
        "official_name": "Welsh assembly",
        "common_name": "Welsh assembly",
        "gss": "W08000001",
        "slug": "naw",
        "territory_code": "WLS",
        "election_name": "National Assembly for Wales election",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": "naw.c.2019-01-17",
      "group_type": null,
      "children": [],
      "elected_role": "Assembly Member",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2016-04-13",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2016 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Mid and West Wales",
        "official_identifier": "gss:W10000006",
        "slug": "mid-and-west-wales",
        "division_type": "WAE",
        "division_subtype": "Welsh Assembly region",
        "division_election_sub_type": "r",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "AMS",
        "name": "Additional Member System",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "naw.r.2019-01-17",
      "tmp_election_id": null,
      "election_title": "(Regions)",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Welsh assembly",
        "election_type": "naw"
      },
      "election_subtype": {
        "name": "Regions",
        "election_subtype": "r"
      },
      "organisation": {
        "official_identifier": "naw",
        "organisation_type": "naw",
        "organisation_subtype": "",
        "official_name": "Welsh assembly",
        "common_name": "Welsh assembly",
        "gss": "W08000001",
        "slug": "naw",
        "territory_code": "WLS",
        "election_name": "National Assembly for Wales election",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": "naw.2019-01-17",
      "group_type": "subtype",
      "children": [
        "naw.r.aberavon.2019-01-17",
        "naw.r.mid-and-west-wales.2019-01-17"
      ],
      "elected_role": "Assembly Member",
      "seats_contested": null,
      "division": null,
      "voting_system": {
        "slug": "AMS",
        "name": "Additional Member System",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "naw.r.aberavon.2019-01-17",
      "tmp_election_id": null,
      "election_title": "Aberavon (Regions)",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Welsh assembly",
        "election_type": "naw"
      },
      "election_subtype": {
        "name": "Regions",
        "election_subtype": "r"
      },
      "organisation": {
        "official_identifier": "naw",
        "organisation_type": "naw",
        "organisation_subtype": "",
        "official_name": "Welsh assembly",
        "common_name": "Welsh assembly",
        "gss": "W08000001",
        "slug": "naw",
        "territory_code": "WLS",
        "election_name": "National Assembly for Wales election",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": "naw.r.2019-01-17",
      "group_type": null,
      "children": [],
      "elected_role": "Assembly Member",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2016-04-13",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2016 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Aberavon",
        "official_identifier": "gss:W09000022",
        "slug": "aberavon",
        "division_type": "WAC",
        "division_subtype": "Welsh Assembly constituency",
        "division_election_sub_type": "c",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "AMS",
        "name": "Additional Member System",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "naw.r.mid-and-west-wales.2019-01-17",
      "tmp_election_id": null,
      "election_title": "Mid and West Wales (Regions)",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Welsh assembly",
        "election_type": "naw"
      },
      "election_subtype": {
        "name": "Regions",
        "election_subtype": "r"
      },
      "organisation": {
        "official_identifier": "naw",
        "organisation_type": "naw",
        "organisation_subtype": "",
        "official_name": "Welsh assembly",
        "common_name": "Welsh assembly",
        "gss": "W08000001",
        "slug": "naw",
        "territory_code": "WLS",
        "election_name": "National Assembly for Wales election",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": "naw.r.2019-01-17",
      "group_type": null,
      "children": [],
      "elected_role": "Assembly Member",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2016-04-13",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2016 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Mid and West Wales",
        "official_identifier": "gss:W10000006",
        "slug": "mid-and-west-wales",
        "division_type": "WAE",
        "division_subtype": "Welsh Assembly region",
        "division_election_sub_type": "r",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "AMS",
        "name": "Additional Member System",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "nia.2019-01-17",
      "tmp_election_id": null,
      "election_title": "",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Northern Ireland assembly",
        "election_type": "nia"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "nia",
        "organisation_type": "nia",
        "organisation_subtype": "",
        "official_name": "Northern Ireland assembly",
        "common_name": "Northern Ireland assembly",
        "gss": "N07000001",
        "slug": "nia",
        "territory_code": "NIR",
        "election_name": "Northern Ireland assembly election",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": null,
      "group_type": "election",
      "children": [
        "nia.lagan-valley.2019-01-17"
      ],
      "elected_role": "Assembly Member",
      "seats_contested": null,
      "division": null,
      "voting_system": null,
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "nia.lagan-valley.2019-01-17",
      "tmp_election_id": null,
      "election_title": "Lagan Valley",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Northern Ireland assembly",
        "election_type": "nia"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "nia",
        "organisation_type": "nia",
        "organisation_subtype": "",
        "official_name": "Northern Ireland assembly",
        "common_name": "Northern Ireland assembly",
        "gss": "N07000001",
        "slug": "nia",
        "territory_code": "NIR",
        "election_name": "Northern Ireland assembly election",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": "nia.2019-01-17",
      "group_type": null,
      "children": [],
      "elected_role": "Assembly Member",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2004-12-02",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2004 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Lagan Valley",
        "official_identifier": "osni_oid:NIE-13",
        "slug": "lagan-valley",
        "division_type": "NIE",
        "division_subtype": "Northern Ireland Assembly constituency",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "NIR"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "parl.2019-01-17",
      "tmp_election_id": null,
      "election_title": "",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "UK Parliament",
        "election_type": "parl"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "parl-hoc",
        "organisation_type": "parl",
        "organisation_subtype": "",
        "official_name": "House of Commons of the United Kingdom",
        "common_name": "House of Commons",
        "gss": "",
        "slug": "parl",
        "territory_code": "GBN",
        "election_name": "UK general election",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": null,
      "group_type": "election",
      "children": [
        "parl.aberavon.2019-01-17",
        "parl.ynys-mon.2019-01-17"
      ],
      "elected_role": "Member of Parliament",
      "seats_contested": null,
      "division": null,
      "voting_system": null,
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "parl.aberavon.2019-01-17",
      "tmp_election_id": null,
      "election_title": "Aberavon",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "UK Parliament",
        "election_type": "parl"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "parl-hoc",
        "organisation_type": "parl",
        "organisation_subtype": "",
        "official_name": "House of Commons of the United Kingdom",
        "common_name": "House of Commons",
        "gss": "",
        "slug": "parl",
        "territory_code": "GBN",
        "election_name": "UK general election",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": "parl.2019-01-17",
      "group_type": null,
      "children": [],
      "elected_role": "Member of Parliament",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2010-07-18",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2010 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Aberavon",
        "official_identifier": "gss:W07000049",
        "slug": "aberavon",
        "division_type": "WMC",
        "division_subtype": "UK Parliament constituency",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "parl.ynys-mon.2019-01-17",
      "tmp_election_id": null,
      "election_title": "Ynys Môn",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "UK Parliament",
        "election_type": "parl"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "parl-hoc",
        "organisation_type": "parl",
        "organisation_subtype": "",
        "official_name": "House of Commons of the United Kingdom",
        "common_name": "House of Commons",
        "gss": "",
        "slug": "parl",
        "territory_code": "GBN",
        "election_name": "UK general election",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": "parl.2019-01-17",
      "group_type": null,
      "children": [],
      "elected_role": "Member of Parliament",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2010-07-18",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2010 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Ynys Môn",
        "official_identifier": "gss:W07000041",
        "slug": "ynys-mon",
        "division_type": "WMC",
        "division_subtype": "UK Parliament constituency",
        "division_election_sub_type": "",
        "seats_total": null,
        "territory_code": "WLS"
      },
      "voting_system": {
        "slug": "FPTP",
        "name": "First-past-the-post",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "pcc.2019-01-17",
      "tmp_election_id": null,
      "election_title": "Police and Crime Commissioner for Avon and Somerset Constabulary",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Police and crime commissioner",
        "election_type": "pcc"
      },
      "election_subtype": null,
      "organisation": null,
      "group": null,
      "group_type": "election",
      "children": [
        "pcc.avon-and-somerset.2019-01-17"
      ],
      "elected_role": "Police and Crime Commissioner",
      "seats_contested": null,
      "division": null,
      "voting_system": null,
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "pcc.avon-and-somerset.2019-01-17",
      "tmp_election_id": null,
      "election_title": "Police and Crime Commissioner for Avon and Somerset Constabulary",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Police and crime commissioner",
        "election_type": "pcc"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "avon-and-somerset",
        "organisation_type": "police_area",
        "organisation_subtype": "",
        "official_name": "Avon and Somerset Constabulary",
        "common_name": "Avon and Somerset Constabulary",
        "gss": "",
        "slug": "avon-and-somerset",
        "territory_code": "ENG",
        "election_name": "Police and Crime Commissioner for Avon and Somerset Constabulary",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": "pcc.2019-01-17",
      "group_type": "organisation",
      "children": [],
      "elected_role": "Police and Crime Commissioner",
      "seats_contested": null,
      "division": null,
      "voting_system": {
        "slug": "sv",
        "name": "Supplementary Vote",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "sp.2019-01-17",
      "tmp_election_id": null,
      "election_title": "",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Scottish parliament",
        "election_type": "sp"
      },
      "election_subtype": null,
      "organisation": {
        "official_identifier": "sp",
        "organisation_type": "sp",
        "organisation_subtype": "",
        "official_name": "Scottish Parliament",
        "common_name": "Scottish Parliament",
        "gss": "S15000001",
        "slug": "sp",
        "territory_code": "SCT",
        "election_name": "Scottish parliament election",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": null,
      "group_type": "election",
      "children": [
        "sp.c.2019-01-17",
        "sp.r.2019-01-17"
      ],
      "elected_role": "Member of the Scottish Parliament",
      "seats_contested": null,
      "division": null,
      "voting_system": null,
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "sp.c.2019-01-17",
      "tmp_election_id": null,
      "election_title": "(Constituencies)",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Scottish parliament",
        "election_type": "sp"
      },
      "election_subtype": {
        "name": "Constituencies",
        "election_subtype": "c"
      },
      "organisation": {
        "official_identifier": "sp",
        "organisation_type": "sp",
        "organisation_subtype": "",
        "official_name": "Scottish Parliament",
        "common_name": "Scottish Parliament",
        "gss": "S15000001",
        "slug": "sp",
        "territory_code": "SCT",
        "election_name": "Scottish parliament election",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": "sp.2019-01-17",
      "group_type": "subtype",
      "children": [
        "sp.c.aberdeen-central.2019-01-17",
        "sp.c.glasgow.2019-01-17"
      ],
      "elected_role": "Member of the Scottish Parliament",
      "seats_contested": null,
      "division": null,
      "voting_system": {
        "slug": "AMS",
        "name": "Additional Member System",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "sp.c.aberdeen-central.2019-01-17",
      "tmp_election_id": null,
      "election_title": "Aberdeen Central (Constituencies)",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Scottish parliament",
        "election_type": "sp"
      },
      "election_subtype": {
        "name": "Constituencies",
        "election_subtype": "c"
      },
      "organisation": {
        "official_identifier": "sp",
        "organisation_type": "sp",
        "organisation_subtype": "",
        "official_name": "Scottish Parliament",
        "common_name": "Scottish Parliament",
        "gss": "S15000001",
        "slug": "sp",
        "territory_code": "SCT",
        "election_name": "Scottish parliament election",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": "sp.c.2019-01-17",
      "group_type": null,
      "children": [],
      "elected_role": "Member of the Scottish Parliament",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2016-04-13",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2016 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Aberdeen Central",
        "official_identifier": "gss:S16000074",
        "slug": "aberdeen-central",
        "division_type": "SPC",
        "division_subtype": "Scottish Parliament constituency",
        "division_election_sub_type": "c",
        "seats_total": null,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "AMS",
        "name": "Additional Member System",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "sp.c.glasgow.2019-01-17",
      "tmp_election_id": null,
      "election_title": "Glasgow (Constituencies)",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Scottish parliament",
        "election_type": "sp"
      },
      "election_subtype": {
        "name": "Constituencies",
        "election_subtype": "c"
      },
      "organisation": {
        "official_identifier": "sp",
        "organisation_type": "sp",
        "organisation_subtype": "",
        "official_name": "Scottish Parliament",
        "common_name": "Scottish Parliament",
        "gss": "S15000001",
        "slug": "sp",
        "territory_code": "SCT",
        "election_name": "Scottish parliament election",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": "sp.c.2019-01-17",
      "group_type": null,
      "children": [],
      "elected_role": "Member of the Scottish Parliament",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2016-04-13",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2016 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Glasgow",
        "official_identifier": "gss:S17000017",
        "slug": "glasgow",
        "division_type": "SPE",
        "division_subtype": "Scottish Parliament region",
        "division_election_sub_type": "r",
        "seats_total": null,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "AMS",
        "name": "Additional Member System",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "sp.r.2019-01-17",
      "tmp_election_id": null,
      "election_title": "(Regions)",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Scottish parliament",
        "election_type": "sp"
      },
      "election_subtype": {
        "name": "Regions",
        "election_subtype": "r"
      },
      "organisation": {
        "official_identifier": "sp",
        "organisation_type": "sp",
        "organisation_subtype": "",
        "official_name": "Scottish Parliament",
        "common_name": "Scottish Parliament",
        "gss": "S15000001",
        "slug": "sp",
        "territory_code": "SCT",
        "election_name": "Scottish parliament election",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": "sp.2019-01-17",
      "group_type": "subtype",
      "children": [
        "sp.r.aberdeen-central.2019-01-17",
        "sp.r.glasgow.2019-01-17"
      ],
      "elected_role": "Member of the Scottish Parliament",
      "seats_contested": null,
      "division": null,
      "voting_system": {
        "slug": "AMS",
        "name": "Additional Member System",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "sp.r.aberdeen-central.2019-01-17",
      "tmp_election_id": null,
      "election_title": "Aberdeen Central (Regions)",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Scottish parliament",
        "election_type": "sp"
      },
      "election_subtype": {
        "name": "Regions",
        "election_subtype": "r"
      },
      "organisation": {
        "official_identifier": "sp",
        "organisation_type": "sp",
        "organisation_subtype": "",
        "official_name": "Scottish Parliament",
        "common_name": "Scottish Parliament",
        "gss": "S15000001",
        "slug": "sp",
        "territory_code": "SCT",
        "election_name": "Scottish parliament election",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": "sp.r.2019-01-17",
      "group_type": null,
      "children": [],
      "elected_role": "Member of the Scottish Parliament",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2016-04-13",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2016 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Aberdeen Central",
        "official_identifier": "gss:S16000074",
        "slug": "aberdeen-central",
        "division_type": "SPC",
        "division_subtype": "Scottish Parliament constituency",
        "division_election_sub_type": "c",
        "seats_total": null,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "AMS",
        "name": "Additional Member System",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    },
    {
      "election_id": "sp.r.glasgow.2019-01-17",
      "tmp_election_id": null,
      "election_title": "Glasgow (Regions)",
      "poll_open_date": "2019-01-17",
      "election_type": {
        "name": "Scottish parliament",
        "election_type": "sp"
      },
      "election_subtype": {
        "name": "Regions",
        "election_subtype": "r"
      },
      "organisation": {
        "official_identifier": "sp",
        "organisation_type": "sp",
        "organisation_subtype": "",
        "official_name": "Scottish Parliament",
        "common_name": "Scottish Parliament",
        "gss": "S15000001",
        "slug": "sp",
        "territory_code": "SCT",
        "election_name": "Scottish parliament election",
        "start_date": "2011-04-01",
        "end_date": null
      },
      "group": "sp.r.2019-01-17",
      "group_type": null,
      "children": [],
      "elected_role": "Member of the Scottish Parliament",
      "seats_contested": null,
      "division": {
        "divisionset": {
          "start_date": "2016-04-13",
          "end_date": null,
          "legislation_url": null,
          "consultation_url": null,
          "short_title": "2016 Boundaries",
          "notes": "Auto imported from http://mapit.mysociety.org"
        },
        "name": "Glasgow",
        "official_identifier": "gss:S17000017",
        "slug": "glasgow",
        "division_type": "SPE",
        "division_subtype": "Scottish Parliament region",
        "division_election_sub_type": "r",
        "seats_total": null,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "AMS",
        "name": "Additional Member System",
        "uses_party_lists": true
      },
      "current": true,
      "explanation": null,
      "cancelled": false
    }
  ]
}
"""
)
no_results = {"count": 0, "next": None, "previous": None, "results": []}

local_highland_parent = json.loads(
    """{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "election_id": "local.2018-12-06",
      "tmp_election_id": null,
      "election_title": "Local elections",
      "poll_open_date": "2018-12-06",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": null,
      "group": "local.2018-12-06",
      "group_type": "organisation",
      "children": [
        "local.highland.2018-12-06"
      ],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": null,
      "voting_system": null,
      "current": true,
      "explanation": null,
      "metadata": null,
      "deleted": true,
      "cancelled": false
    }
  ]
}
    """
)

local_highland = json.loads(
    """
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "election_id": "local.highland.2018-12-06",
      "tmp_election_id": null,
      "election_title": "Highland local election",
      "poll_open_date": "2018-12-06",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "url": "http://127.0.0.1:8001/api/organisations/local-authority/HLD/1996-04-01.json",
        "official_identifier": "HLD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Highland Council",
        "common_name": "Highland",
        "slug": "highland",
        "territory_code": "SCT",
        "election_name": "Highland local election",
        "start_date": "1996-04-01",
        "end_date": null
      },
      "group": "local.2018-12-06",
      "group_type": "organisation",
      "children": [
        "local.highland.wester-ross-strathpeffer-and-lochalsh.by.2018-12-06"
      ],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": null,
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "metadata": null,
      "deleted": true,
      "cancelled": false
    },
    {
      "election_id": "local.highland.wester-ross-strathpeffer-and-lochalsh.by.2018-12-06",
      "tmp_election_id": null,
      "election_title": "Highland local election Wester Ross, Strathpeffer and Lochalsh by-election",
      "poll_open_date": "2018-12-06",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "url": "http://127.0.0.1:8001/api/organisations/local-authority/HLD/1996-04-01.json",
        "official_identifier": "HLD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Highland Council",
        "common_name": "Highland",
        "slug": "highland",
        "territory_code": "SCT",
        "election_name": "Highland local election",
        "start_date": "1996-04-01",
        "end_date": null
      },
      "group": "local.highland.2018-12-06",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": 1,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/278/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/highland/",
          "short_title": "The Highland (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Wester Ross, Strathpeffer and Lochalsh",
        "official_identifier": "gss:S13002994",
        "slug": "wester-ross-strathpeffer-and-lochalsh",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "metadata": null,
      "deleted": true,
      "cancelled": false
    }
  ]
}"""
)
duplicate_post_names_parent = json.loads(
    """{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "election_id": "local.2019-05-02",
      "tmp_election_id": null,
      "election_title": "Local elections",
      "poll_open_date": "2019-05-02",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": null,
      "group": "local.2019-05-02",
      "group_type": "organisation",
      "children": [
        "local.surrey-heath.2019-05-02",
        "local.allerdale.2019-05-02"
      ],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": null,
      "voting_system": null,
      "current": true,
      "explanation": null,
      "metadata": null,
      "deleted": false,
      "cancelled": false,
      "replaces": null,
      "replaced_by": null
    }
  ]
}
    """
)
duplicate_post_names = json.loads(
    """{
    "count": 4,
    "next": null,
    "previous": null,
    "results": [{
            "election_id": "local.surrey-heath.2019-05-02",
            "tmp_election_id": null,
            "election_title": "Surrey Heath local election",
            "poll_open_date": "2019-05-02",
            "election_type": {
                "name": "Local elections",
                "election_type": "local"
            },
            "election_subtype": null,
            "organisation": {
                "url": "https://elections.democracyclub.org.uk/api/organisations/local-authority/SUR/1974-04-01/",
                "official_identifier": "SUR",
                "organisation_type": "local-authority",
                "organisation_subtype": "NMD",
                "official_name": "Surrey Heath Borough Council",
                "common_name": "Surrey Heath",
                "slug": "surrey-heath",
                "territory_code": "ENG",
                "election_name": "Surrey Heath local election",
                "start_date": "1974-04-01",
                "end_date": null
            },
            "group": "local.2019-05-02",
            "group_type": "organisation",
            "children": [
                "local.surrey-heath.st-michaels.2019-05-02"
            ],
            "elected_role": "Local Councillor",
            "seats_contested": null,
            "division": null,
            "voting_system": {
                "slug": "FPTP",
                "name": "First-past-the-post",
                "uses_party_lists": false
            },
            "current": true,
            "explanation": null,
            "metadata": null,
            "deleted": false,
            "cancelled": false,
            "replaces": null,
            "replaced_by": null
        },
        {
            "election_id": "local.surrey-heath.st-michaels.2019-05-02",
            "tmp_election_id": null,
            "election_title": "Surrey Heath local election St Michaels",
            "poll_open_date": "2019-05-02",
            "election_type": {
                "name": "Local elections",
                "election_type": "local"
            },
            "election_subtype": null,
            "organisation": {
                "url": "https://elections.democracyclub.org.uk/api/organisations/local-authority/SUR/1974-04-01/",
                "official_identifier": "SUR",
                "organisation_type": "local-authority",
                "organisation_subtype": "NMD",
                "official_name": "Surrey Heath Borough Council",
                "common_name": "Surrey Heath",
                "slug": "surrey-heath",
                "territory_code": "ENG",
                "election_name": "Surrey Heath local election",
                "start_date": "1974-04-01",
                "end_date": null
            },
            "group": "local.surrey-heath.2019-05-02",
            "group_type": null,
            "children": [],
            "elected_role": "Local Councillor",
            "seats_contested": 2,
            "division": {
                "divisionset": {
                    "start_date": "2019-05-02",
                    "end_date": null,
                    "legislation_url": "http://www.legislation.gov.uk/uksi/2017/1268/contents/made",
                    "consultation_url": "http://www.lgbce.org.uk/current-reviews/south-east/surrey/surrey-heath",
                    "short_title": "The Surrey Heath (Electoral Changes) Order 2017",
                    "notes": ""
                },
                "name": "St Michaels",
                "official_identifier": "SUR:st-michaels",
                "slug": "st-michaels",
                "division_type": "DIW",
                "division_subtype": "",
                "division_election_sub_type": "",
                "seats_total": 2,
                "territory_code": "ENG"
            },
            "voting_system": {
                "slug": "FPTP",
                "name": "First-past-the-post",
                "uses_party_lists": false
            },
            "current": true,
            "explanation": null,
            "metadata": null,
            "deleted": false,
            "cancelled": false,
            "replaces": null,
            "replaced_by": null
        },
        {
            "election_id": "local.allerdale.2019-05-02",
            "tmp_election_id": null,
            "election_title": "Allerdale local election",
            "poll_open_date": "2019-05-02",
            "election_type": {
                "name": "Local elections",
                "election_type": "local"
            },
            "election_subtype": null,
            "organisation": {
                "url": "https://elections.democracyclub.org.uk/api/organisations/local-authority/ALL/1974-04-01/",
                "official_identifier": "ALL",
                "organisation_type": "local-authority",
                "organisation_subtype": "NMD",
                "official_name": "Allerdale Borough Council",
                "common_name": "Allerdale",
                "slug": "allerdale",
                "territory_code": "ENG",
                "election_name": "Allerdale local election",
                "start_date": "1974-04-01",
                "end_date": null
            },
            "group": "local.2019-05-02",
            "group_type": "organisation",
            "children": [
                "local.allerdale.st-michaels.2019-05-02"
            ],
            "elected_role": "Local Councillor",
            "seats_contested": null,
            "division": null,
            "voting_system": {
                "slug": "FPTP",
                "name": "First-past-the-post",
                "uses_party_lists": false
            },
            "current": true,
            "explanation": null,
            "metadata": null,
            "deleted": false,
            "cancelled": false,
            "replaces": null,
            "replaced_by": null
        },
        {
            "election_id": "local.allerdale.st-michaels.2019-05-02",
            "tmp_election_id": null,
            "election_title": "Allerdale local election St Michael's",
            "poll_open_date": "2019-05-02",
            "election_type": {
                "name": "Local elections",
                "election_type": "local"
            },
            "election_subtype": null,
            "organisation": {
                "url": "https://elections.democracyclub.org.uk/api/organisations/local-authority/ALL/1974-04-01/",
                "official_identifier": "ALL",
                "organisation_type": "local-authority",
                "organisation_subtype": "NMD",
                "official_name": "Allerdale Borough Council",
                "common_name": "Allerdale",
                "slug": "allerdale",
                "territory_code": "ENG",
                "election_name": "Allerdale local election",
                "start_date": "1974-04-01",
                "end_date": null
            },
            "group": "local.allerdale.2019-05-02",
            "group_type": null,
            "children": [],
            "elected_role": "Local Councillor",
            "seats_contested": 2,
            "division": {
                "divisionset": {
                    "start_date": "2019-05-02",
                    "end_date": null,
                    "legislation_url": "http://www.legislation.gov.uk/uksi/2017/1067/contents/made",
                    "consultation_url": "http://www.lgbce.org.uk/current-reviews/north-west/cumbria/allerdale",
                    "short_title": "The Allerdale (Electoral Changes) Order 2017",
                    "notes": ""
                },
                "name": "St Michael's",
                "official_identifier": "ALL:st-michaels",
                "slug": "st-michaels",
                "division_type": "DIW",
                "division_subtype": "",
                "division_election_sub_type": "",
                "seats_total": 2,
                "territory_code": "ENG"
            },
            "voting_system": {
                "slug": "FPTP",
                "name": "First-past-the-post",
                "uses_party_lists": false
            },
            "current": true,
            "explanation": null,
            "metadata": null,
            "deleted": false,
            "cancelled": false,
            "replaces": null,
            "replaced_by": null
        }
    ]
}
"""
)

get_changing_identifier_code_result_parent = json.loads(
    """
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [{
            "election_id": "local.2019-05-02",
            "tmp_election_id": null,
            "election_title": "Local elections",
            "poll_open_date": "2019-05-02",
            "election_type": {
                "name": "Local elections",
                "election_type": "local"
            },
            "election_subtype": null,
            "organisation": null,
            "group": "local.2019-05-02",
            "group_type": "organisation",
            "children": [
                "local.surrey-heath.2019-05-02"
            ],
            "elected_role": "Local Councillor",
            "seats_contested": null,
            "division": null,
            "voting_system": null,
            "current": true,
            "explanation": null,
            "metadata": null,
            "deleted": false,
            "cancelled": false,
            "replaces": null,
            "replaced_by": null
        }
    ]
}
"""
)


def get_changing_identifier_code_result(identifier):
    string = """{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [{
            "election_id": "local.surrey-heath.2019-05-02",
            "tmp_election_id": null,
            "election_title": "Surrey Heath local election",
            "poll_open_date": "2019-05-02",
            "election_type": {
                "name": "Local elections",
                "election_type": "local"
            },
            "election_subtype": null,
            "organisation": {
                "url": "https://elections.democracyclub.org.uk/api/organisations/local-authority/SUR/1974-04-01/",
                "official_identifier": "SUR",
                "organisation_type": "local-authority",
                "organisation_subtype": "NMD",
                "official_name": "Surrey Heath Borough Council",
                "common_name": "Surrey Heath",
                "slug": "surrey-heath",
                "territory_code": "ENG",
                "election_name": "Surrey Heath local election",
                "start_date": "1974-04-01",
                "end_date": null
            },
            "group": "local.2019-05-02",
            "group_type": "organisation",
            "children": [
                "local.surrey-heath.st-michaels.2019-05-02"
            ],
            "elected_role": "Local Councillor",
            "seats_contested": null,
            "division": null,
            "voting_system": {
                "slug": "FPTP",
                "name": "First-past-the-post",
                "uses_party_lists": false
            },
            "current": true,
            "explanation": null,
            "metadata": null,
            "deleted": false,
            "cancelled": false,
            "replaces": null,
            "replaced_by": null
        },
        {
            "election_id": "local.surrey-heath.st-michaels.2019-05-02",
            "tmp_election_id": null,
            "election_title": "Surrey Heath local election St Michael's",
            "poll_open_date": "2019-05-02",
            "election_type": {
                "name": "Local elections",
                "election_type": "local"
            },
            "election_subtype": null,
            "organisation": {
                "url": "https://elections.democracyclub.org.uk/api/organisations/local-authority/SUR/1974-04-01/",
                "official_identifier": "SUR",
                "organisation_type": "local-authority",
                "organisation_subtype": "NMD",
                "official_name": "Surrey Heath Borough Council",
                "common_name": "Surrey Heath",
                "slug": "surrey-heath",
                "territory_code": "ENG",
                "election_name": "Surrey Heath local election",
                "start_date": "1974-04-01",
                "end_date": null
            },
            "group": "local.surrey-heath.2019-05-02",
            "group_type": null,
            "children": [],
            "elected_role": "Local Councillor",
            "seats_contested": 2,
            "division": {
                "divisionset": {
                    "start_date": "2019-05-02",
                    "end_date": null,
                    "legislation_url": "",
                    "consultation_url": "",
                    "short_title": "The Surrey Heath (Electoral Changes) Order 2017",
                    "notes": ""
                },
                "name": "St Michael's",
                "official_identifier": "##########",
                "slug": "st-michaels",
                "division_type": "DIW",
                "division_subtype": "",
                "division_election_sub_type": "",
                "seats_total": 2,
                "territory_code": "ENG"
            },
            "voting_system": {
                "slug": "FPTP",
                "name": "First-past-the-post",
                "uses_party_lists": false
            },
            "current": true,
            "explanation": null,
            "metadata": null,
            "deleted": false,
            "cancelled": false,
            "replaces": null,
            "replaced_by": null
        }
        ]
}
    """.replace("##########", identifier)
    return json.loads(string)


pre_gss_result = get_changing_identifier_code_result("SUR:st-michaels")
post_gss_result = get_changing_identifier_code_result("gss:E05010885")

replaced_election_parents = json.loads(
    """
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "election_id": "local.2018-12-06",
      "tmp_election_id": null,
      "election_title": "Local elections",
      "poll_open_date": "2018-12-06",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": null,
      "group": "local.2018-12-06",
      "group_type": "organisation",
      "children": [
        "local.highland.2018-12-06"
      ],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": null,
      "voting_system": null,
      "current": true,
      "explanation": null,
      "metadata": null,
      "deleted": true,
      "cancelled": false
    }
    ]

}
"""
)

replaced_election = json.loads(
    """
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "election_id": "local.highland.2018-12-06",
      "tmp_election_id": null,
      "election_title": "Highland local election",
      "poll_open_date": "2018-12-06",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "url": "http://127.0.0.1:8001/api/organisations/local-authority/HLD/1996-04-01.json",
        "official_identifier": "HLD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Highland Council",
        "common_name": "Highland",
        "slug": "highland",
        "territory_code": "SCT",
        "election_name": "Highland local election",
        "start_date": "1996-04-01",
        "end_date": null
      },
      "group": "local.2018-12-06",
      "group_type": "organisation",
      "children": [
        "local.highland.wester-ross-strathpeffer-and-lochalsh.by.2018-12-06"
      ],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": null,
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "metadata": null,
      "deleted": true,
      "cancelled": false
    },
    {
      "election_id": "local.highland.wester-ross-strathpeffer-and-lochalsh.by.2018-12-06",
      "tmp_election_id": null,
      "election_title": "Highland local election Wester Ross, Strathpeffer and Lochalsh by-election",
      "poll_open_date": "2018-12-06",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "url": "http://127.0.0.1:8001/api/organisations/local-authority/HLD/1996-04-01.json",
        "official_identifier": "HLD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Highland Council",
        "common_name": "Highland",
        "slug": "highland",
        "territory_code": "SCT",
        "election_name": "Highland local election",
        "start_date": "1996-04-01",
        "end_date": null
      },
      "group": "local.highland.2018-12-06",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": 1,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/278/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/highland/",
          "short_title": "The Highland (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Wester Ross, Strathpeffer and Lochalsh",
        "official_identifier": "gss:S13002994",
        "slug": "wester-ross-strathpeffer-and-lochalsh",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "metadata": null,
      "deleted": true,
      "cancelled": false,
      "replaces": "local.highland.wester-ross-strathpeffer-and-lochalsh.by.2017-12-06"
    }
  ]
}"""
)

duplicate_post_and_election_parents = json.loads(
    """
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "election_id": "local.2018-12-06",
      "tmp_election_id": null,
      "election_title": "Local elections",
      "poll_open_date": "2018-12-06",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": null,
      "group": "local.2018-12-06",
      "group_type": "organisation",
      "children": [
        "local.highland.2018-12-06"
      ],
      "elected_role": null,
      "seats_contested": null,
      "division": null,
      "voting_system": null,
      "current": true,
      "explanation": null,
      "metadata": null,
      "deleted": true,
      "cancelled": false
    }
    ]}


"""
)

duplicate_post_and_election = json.loads(
    """
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "election_id": "local.highland.2018-12-06",
      "tmp_election_id": null,
      "election_title": "Highland local election",
      "poll_open_date": "2018-12-06",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "url": "http://127.0.0.1:8001/api/organisations/local-authority/HLD/1996-04-01.json",
        "official_identifier": "HLD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Highland Council",
        "common_name": "Highland",
        "slug": "highland",
        "territory_code": "SCT",
        "election_name": "Highland local election",
        "start_date": "1996-04-01",
        "end_date": null
      },
      "group": "local.2018-12-06",
      "group_type": "organisation",
      "children": [
        "local.highland.wester-ross-strathpeffer-and-lochalsh.by.2018-12-06",
        "local.highland.wester-ross-strathpeffer-and-lochalsh.2018-12-06"
      ],
      "elected_role": "Local Councillor",
      "seats_contested": null,
      "division": null,
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "metadata": null,
      "deleted": true,
      "cancelled": false
    },
    {
      "election_id": "local.highland.wester-ross-strathpeffer-and-lochalsh.2018-12-06",
      "tmp_election_id": null,
      "election_title": "Highland local election Wester Ross, Strathpeffer and Lochalsh by-election",
      "poll_open_date": "2018-12-06",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "url": "http://127.0.0.1:8001/api/organisations/local-authority/HLD/1996-04-01.json",
        "official_identifier": "HLD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Highland Council",
        "common_name": "Highland",
        "slug": "highland",
        "territory_code": "SCT",
        "election_name": "Highland local election",
        "start_date": "1996-04-01",
        "end_date": null
      },
      "group": "local.highland.2018-12-06",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": 1,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/278/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/highland/",
          "short_title": "The Highland (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Wester Ross, Strathpeffer and Lochalsh",
        "official_identifier": "gss:S13002994",
        "slug": "wester-ross-strathpeffer-and-lochalsh",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "metadata": null,
      "deleted": true,
      "cancelled": true,
      "replaces": null
    },
    {
      "election_id": "local.highland.wester-ross-strathpeffer-and-lochalsh.by.2018-12-06",
      "tmp_election_id": null,
      "election_title": "Highland local election Wester Ross, Strathpeffer and Lochalsh by-election",
      "poll_open_date": "2018-12-06",
      "election_type": {
        "name": "Local elections",
        "election_type": "local"
      },
      "election_subtype": null,
      "organisation": {
        "url": "http://127.0.0.1:8001/api/organisations/local-authority/HLD/1996-04-01.json",
        "official_identifier": "HLD",
        "organisation_type": "local-authority",
        "organisation_subtype": "CA",
        "official_name": "The Highland Council",
        "common_name": "Highland",
        "slug": "highland",
        "territory_code": "SCT",
        "election_name": "Highland local election",
        "start_date": "1996-04-01",
        "end_date": null
      },
      "group": "local.highland.2018-12-06",
      "group_type": null,
      "children": [],
      "elected_role": "Local Councillor",
      "seats_contested": 1,
      "division": {
        "divisionset": {
          "start_date": "2017-05-04",
          "end_date": null,
          "legislation_url": "http://www.legislation.gov.uk/ssi/2016/278/contents/made",
          "consultation_url": "http://www.lgbc-scotland.gov.uk/reviews/5th_electoral/highland/",
          "short_title": "The Highland (Electoral Arrangements) Order 2016",
          "notes": ""
        },
        "name": "Wester Ross, Strathpeffer and Lochalsh",
        "official_identifier": "gss:S13002994",
        "slug": "wester-ross-strathpeffer-and-lochalsh",
        "division_type": "UTW",
        "division_subtype": "",
        "division_election_sub_type": "",
        "seats_total": 4,
        "territory_code": "SCT"
      },
      "voting_system": {
        "slug": "STV",
        "name": "Single Transferable Vote",
        "uses_party_lists": false
      },
      "current": true,
      "explanation": null,
      "metadata": null,
      "deleted": true,
      "cancelled": false,
      "replaces": null
    }
  ]
}"""
)
