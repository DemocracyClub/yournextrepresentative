PEOPLE_LIABLE_TO_VANDALISM = {
    2811,  # Theresa May
    1120,  # Jeremy Corbyn
    4546,  # Boris Johnson
    6035,  # Paul Nuttall
    8372,  # Nicola Sturgeon
    737,  # Ruth Davidson
    34605,  # Matt Furey-King (due to a vandalism incident)
    31705,  # Lance Charles Quantrill (due to a vandalism incident)
    1528,  # Janus Polenceus
    25402,  # Giles Game
    4230,  # Craig Mackinlay
    # Below we include the person ID of anyone who is currently a minister.
    # This list was generated from:
    #
    #   https://github.com/mysociety/parlparse/blob/master/members/ministers-2010.json
    #
    # ... with this snippet of Python:
    #
    # import datetime, json
    # with open(ministers-2010.json') as f:
    #     ministers = json.load(f)
    # for m in ministers['memberships']:
    #     if not re.search(r'^(Minister|The Secretary of State|Deputy Prime Minister|The Prime Minister)', m.get('role', '')):
    #         continue
    #     today = str(date.today())
    #     if not (today >= m['start_date'] and today <= m.get('end_date', '9999-12-31')):
    #         continue
    #     i = Identifier.objects.filter(identifier=m['person_id']).first()
    #     if i is None:
    #         continue
    #     person = i.content_object
    #     print '    {0}, # {1} ({2})'.format(person.id, person.name, m['role'])
    1018,  # Anne Milton (Minister of State (Education))
    1104,  # Edward Timpson (Minister of State (Department for Education))
    1303,  # Karen Bradley (The Secretary of State for Northern Ireland)
    1326,  # Priti Patel (The Secretary of State for International Development)
    1476,  # Harriett Baldwin (Minister of State (Foreign and Commonwealth Office) (Joint with the Department for International Development))
    155,  # John Glen (Minister of State (Treasury) (City))
    1557,  # George Hollingbery (Minister of State (International Trade))
    1573,  # Claire Perry (Minister of State (Business, Energy and Industrial Strategy) (Energy and Clean Growth))
    1592,  # David Mundell (The Secretary of State for Scotland)
    1604,  # Jeremy Wright (The Secretary of State for Digital, Culture, Media and Sport)
    1692,  # Penny Mordaunt (The Secretary of State for International Development)
    1918,  # Greg Clark (The Secretary of State for Business, Energy and Industrial Strategy )
    1923,  # Alun Cairns (The Secretary of State for Wales)
    212,  # Alan Duncan (Minister of State)
    2204,  # Jo Johnson (Minister of State (Department for Education) (Universities and Science) (Joint with the Department for Business, Energy and Industrial Strategy))
    2253,  # Stephen Hammond (Minister of State (Department of Health and Social Care))
    239,  # Stephen Barclay (The Secretary of State for Exiting the European Union)
    2534,  # James Brokenshire (The Secretary of State for Housing, Communities and Local Government)
    2811,  # Theresa May (The Prime Minister)
    2832,  # Michael Fallon (The Secretary of State for Defence)
    2875,  # Andrea Leadsom (The Secretary of State for Environment, Food and Rural Affairs)
    2885,  # David Davis (The Secretary of State for Exiting the European Union)
    2937,  # Caroline Dinenage (Minister of State (Department of Health and Social Care))
    3151,  # David Jones (Minister of State (Department for Exiting the European Union))
    3155,  # Jeremy Hunt (The Secretary of State for Health)
    3238,  # Ben Wallace (Minister of State (Home Office) (Security))
    3284,  # Chris Grayling (The Secretary of State for Transport)
    3417,  # Jesse Norman (Minister of State (Department for Transport))
    3445,  # John Hayes (Minister of State (Department for Transport))
    3449,  # Damian Hinds (The Secretary of State for Education)
    3486,  # Damian Green (The Secretary of State for Work and Pensions)
    349,  # Sajid Javid (The Secretary of State for the Home Department)
    3533,  # Brandon Lewis (Minister without Portfolio )
    3737,  # Matthew Hancock (Minister of State (Department for Culture, Media and Sport) (Digital Policy))
    3741,  # Robert Halfon (Minister of State (Department of Education) (Apprenticeships and Skills))
    3745,  # Chris Skidmore (Minister of State (Department for Business, Energy and Industrial Strategy) (Universities and Science) (Joint with the Department for Education))
    4014,  # Michael Gove (The Secretary of State for Environment, Food and Rural Affairs)
    4021,  # Justine Greening (The Secretary of State for Education)
    4099,  # David Lidington (Minister of State (Cabinet Office))
    451,  # Liam Fox (The Secretary of State for International Trade and President of the Board of Trade)
    4881,  # Gavin Barwell (Minister of State (Department for Communities and Local Government) (Housing, Planning and London))
    4893,  # Victoria Atkins (Minister for Women)
    519,  # Amber Rudd (The Secretary of State for Work and Pensions)
    5272,  # Kit Malthouse (Minister of State (Housing, Communities and Local Government))
    600,  # Mark Field (Minister of State)
    769,  # Gavin Williamson (The Secretary of State for Defence)
    918,  # Nick Gibb (Minister of State (Education))
    # europarl.2019-05-023 MEP candidates in list position 1
    11857,  # Colum Eastwood
    12218,  # Magid Magid
    12326,  # Shaffaq Mohammed
    1516,  # Donald Mackay
    16,  # Stephen Dorrell
    183,  # Gerard Batten
    19920,  # Jackie Jones
    21119,  # Barbara Gibson
    2126,  # Stuart Agnew
    2351,  # Mike Hookem
    2454,  # Naomi Long
    26664,  # Caroline Voaden
    26849,  # Sam Bennett
    31,  # Danny Kennedy
    34111,  # Molly Scott Cato
    34506,  # Bill Newton Dunn
    34830,  # Fiona Hall
    3526,  # Lawrence Webb
    3594,  # Richard Elvin
    36075,  # Irina von Wiese
    37323,  # Scott Ainslie
    5247,  # Piers Wauchope
    5824,  # Clare Bailey
    5828,  # Ernest John Valentine
    5998,  # Catherine Rowett
    6550,  # Robert Hill
    67695,  # Alexandra Phillips
    6951,  # Phil Bennion
    69533,  # Jill Evans
    69537,  # Catherine Bearder
    69696,  # Emma McClarkin
    69708,  # Syed Salah Kamall
    69720,  # Sajjad Karim
    69730,  # Nosheena Mobarik
    69734,  # Daniel Hannan
    69744,  # Ashley Fox
    69943,  # Rory Palmer
    69948,  # Alex Mayer
    69954,  # Claude Moraes
    69962,  # Judith Kirton-Darling
    69965,  # Theresa Griffin
    69973,  # David Martin
    69980,  # John Howarth
    69989,  # Clare Moody
    69999,  # Neena Gill
    70007,  # Richard Corbett
    70035,  # Chris Davies
    7011,  # Stephen Morris
    70176,  # Alyn Smith
    70323,  # Alan Graves Snr
    70325,  # Adam Richardson
    70336,  # Kris Hicks
    70343,  # Sheila Ritchie
    70354,  # Rachel Johnson
    70360,  # Catherine Mayer
    70367,  # Neville Seed
    70368,  # Mothiur Rahman
    70369,  # Larch Ian Albert Frank Maxey
    70370,  # Gavin Esler
    70375,  # Ann Widdecombe
    70381,  # Andrea Cooper
    70399,  # Claire Regina Fox
    70407,  # Sophie Catherine Larroque
    70408,  # Neil Patrick McCann
    70413,  # Kate Godfrey
    70430,  # Pierre Edmond Kirk
    70447,  # Benyamin Naeem Habib
    7065,  # Amandeep Singh Bhogal
    7233,  # Jenny Knight
    7400,  # Vanessa Helen Hudson
    986,  # Gina Dowding
    70456,  # Tommy Robinson
    70330,  # Mark Meechan (alias CountDankula)
    70334,  # Carl Benjamin (alias Sargon of Akkad)
    70307,  # Andrew Adonis (alias Lord Adonis)
}
