import os

from django.core.management.base import BaseCommand

import resultsbot
from resultsbot.importers.modgov import ModGovElectionMatcher

import csv

data = [

    ['local.woking.2018-05-03', 'moderngov.woking.gov.uk'],
    ['local.wokingham.2018-05-03', 'wokingham.moderngov.co.uk'],
    ['local.wolverhampton.2018-05-03', 'wolverhampton.moderngov.co.uk'],
    ['local.worcester.2018-05-03', 'worcestershire.moderngov.co.uk'],


    ['local.barking-and-dagenham.2018-05-03', 'modgov.lbbd.gov.uk/internet/'],
    # ['local.barnet.2018-05-03', 'barnet.moderngov.co.uk'], They don't seem to use the election feature
    ['local.bromley.2018-05-03', 'cds.bromley.gov.uk'],
    ['local.brent.2018-05-03', 'democracy.brent.gov.uk'],
    # ['local.camden.2018-05-03', 'democracy.camden.gov.uk'],
    # ['local.croydon.2018-05-03', 'democracy.croydon.gov.uk'],
    ['local.enfield.2018-05-03', 'governance.enfield.gov.uk'],
    ['local.epping-forest.2018-05-03', 'rds.eppingforestdc.gov.uk'],
    # ['local.hackney.2018-05-03', 'mginternet.hackney.gov.uk'],
    # ['local.greenwich.2018-05-03', 'committees.greenwich.gov.uk'],
    # ['local.hammersmith-and-fulham.2018-05-03', 'democracy.lbhf.gov.uk/'],
    # ['local.haringey.2018-05-03', 'www.minutes.haringey.gov.uk'],
    ['local.harrow.2018-05-03', 'www.harrow.gov.uk/www2'],
    # ['local.havant.2018-05-03', 'havant.moderngov.co.uk'],
    # ['local.hillingdon.2018-05-03', 'modgov.hillingdon.gov.uk'],
    # ['local.islington.2018-05-03', 'democracy.islington.gov.uk'],
    ['local.kingston-upon-thames.2018-05-03', 'moderngov.kingston.gov.uk'],
    ['local.lambeth.2018-05-03', 'moderngov.lambeth.gov.uk'],
    ['local.lewisham.2018-05-03', 'councilmeetings.lewisham.gov.uk'],
    ['local.merton.2018-05-03', 'merton.moderngov.co.uk'],
    ['local.newham.2018-05-03', 'mgov.newham.gov.uk'],
    # ['local.redbridge.2018-05-03', 'moderngov.redbridge.gov.uk'],
    ['local.richmond-upon-thames.2018-05-03', 'cabnet.richmond.gov.uk'],
    # ['local.southwark.2018-05-03', 'moderngov.southwark.gov.uk'],
    ['local.sutton.2018-05-03', 'moderngov.sutton.gov.uk'],
    ['local.swindon.2018-05-03', 'ww5.swindon.gov.uk/moderngov'],
    ['local.tower-hamlets.2018-05-03', 'moderngov.towerhamlets.gov.uk'],
    ['local.wandsworth.2018-05-03', 'democracy.wandsworth.gov.uk'],
    # ['local.watford.2018-05-03', 'watford.moderngov.co.uk'],
    ['local.westminster.2018-05-03', 'committees.westminster.gov.uk'],

    ['local.aylesbury-vale.2018-05-03', 'aylesburyvale.moderngov.co.uk'],
    ['local.eastleigh.2018-05-03', 'meetings.eastleigh.gov.uk'],
    # ['local.barnsley.2018-05-03', 'barnsleymbc.moderngov.co.uk'],
    ['local.basildon.2018-05-03', 'www.basildonmeetings.info'],
    ['local.basingstoke-and-deane.2018-05-03', 'democracy.basingstoke.gov.uk'],
    ['local.bexley.2018-05-03', 'democracy.bexley.gov.uk'],
    ['local.bradford.2018-05-03', 'bradford.moderngov.co.uk'],
    ['local.brentwood.2018-05-03', 'brentwood.moderngov.co.uk'],
    ['local.burnley.2018-05-03', 'burnley.moderngov.co.uk'],
    ['local.bury.2018-05-03', 'councildecisions.bury.gov.uk'],
    ['local.cambridge.2018-05-03', 'democracy.cambridge.gov.uk'],
    ['local.cheltenham.2018-05-03', 'democracy.cheltenham.gov.uk'],
    ['local.cherwell.2018-05-03', 'modgov.cherwell.gov.uk'],
    ['local.cheshire-west-and-chester.2018-05-03', 'cmttpublic.cheshirewestandchester.gov.uk'],
    ['local.chorley.2018-05-03', 'democracy.chorley.gov.uk'],
    ['local.city-of-lincoln.2018-05-03', 'democratic.lincoln.gov.uk'],
    ['local.coventry.2018-05-03', 'moderngov.coventry.gov.uk'],
    ['local.crawley.2018-05-03', 'democracy.crawley.gov.uk'],
    ['local.elmbridge.2018-05-03', 'mygov.elmbridge.gov.uk'],
    ['local.exeter.2018-05-03', 'committees.exeter.gov.uk'],
    ['local.fareham.2018-05-03', 'moderngov.fareham.gov.uk'],
    ['local.halton.2018-05-03', 'moderngov.halton.gov.uk'],
    ['local.harlow.2018-05-03', 'moderngov.harlow.gov.uk'],
    ['local.hastings.2018-05-03', 'hastings.moderngov.co.uk'],
    ['local.havering.2018-05-03', 'democracy.havering.gov.uk'],
    ['local.hounslow.2018-05-03', 'democraticservices.hounslow.gov.uk'],
    ['local.huntingdonshire.2018-05-03', 'applications.huntingdonshire.gov.uk/moderngov'],
    ['local.hyndburn.2018-05-03', 'democracy.hyndburnbc.gov.uk'],
    ['local.ipswich.2018-05-03', 'democracy.ipswich.gov.uk'],
    ['local.kirklees.2018-05-03', 'democracy.kirklees.gov.uk'],
    ['local.knowsley.2018-05-03', 'councillors.knowsley.gov.uk'],
    ['local.leeds.2018-05-03', 'democracy.leeds.gov.uk'],
    ['local.leicestershire.2018-05-03', 'politics.leics.gov.uk'],
    ['local.liverpool.2018-05-03', 'councillors.liverpool.gov.uk'],
    ['local.maidstone.2018-05-03', 'meetings.maidstone.gov.uk'],
    ['local.newcastle-under-lyme.2018-05-03', 'moderngov.newcastle-staffs.gov.uk'],
    ['local.newcastle-upon-tyne.2018-05-03', 'democracy.newcastle.gov.uk'],
    ['local.north-hertfordshire.2018-05-03', 'democracy.north-herts.gov.uk'],
    ['local.oldham.2018-05-03', 'committees.oldham.gov.uk'],
    ['local.oxford.2018-05-03', 'mycouncil.oxford.gov.uk'],
    ['local.peterborough.2018-05-03', 'democracy.peterborough.gov.uk'],
    ['local.plymouth.2018-05-03', 'democracy.plymouth.gov.uk'],
    ['local.portsmouth.2018-05-03', 'democracy.portsmouth.gov.uk'],
    ['local.preston.2018-05-03', 'preston.moderngov.co.uk'],
    ['local.redditch.2018-05-03', 'moderngovwebpublic.redditchbc.gov.uk'],
    ['local.reigate-and-banstead.2018-05-03', 'reigate-banstead.moderngov.co.uk'],
    ['local.rochdale.2018-05-03', 'democracy.rochdale.gov.uk'],
    ['local.salford.2018-05-03', 'sccdemocracy.salford.gov.uk'],
    ['local.sefton.2018-05-03', 'modgov.sefton.gov.uk/moderngov'],
    ['local.sheffield.2018-05-03', 'democracy.sheffield.gov.uk'],
    ['local.slough.2018-05-03', 'www.slough.gov.uk/moderngov'],
    ['local.solihull.2018-05-03', 'eservices.solihull.gov.uk/mginternet'],
    ['local.south-cambridgeshire.2018-05-03', 'scambs.moderngov.co.uk'],
    ['local.south-holland.2018-05-03', 'democracy.sholland.gov.uk'],
    ['local.south-lakeland.2018-05-03', 'democracy.southlakeland.gov.uk'],
    ['local.southampton.2018-05-03', 'www.southampton.gov.uk/moderngov'],
    ['local.southend-on-sea.2018-05-03', 'democracy.southend.gov.uk'],
    ['local.st-albans.2018-05-03', 'stalbans.moderngov.co.uk'],
    ['local.st-helens.2018-05-03', 'moderngov.sthelens.gov.uk'],
    ['local.stevenage.2018-05-03', 'democracy.stevenage.gov.uk'],
    ['local.stockport.2018-05-03', 'democracy.stockport.gov.uk'],
    ['local.swale.2018-05-03', 'services.swale.gov.uk/meetings'],
    ['local.tameside.2018-05-03', 'tameside.moderngov.co.uk'],
    ['local.tamworth.2018-05-03', 'democracy.tamworth.gov.uk'],
    ['local.thurrock.2018-05-03', 'democracy.thurrock.gov.uk'],
    ['local.trafford.2018-05-03', 'democratic.trafford.gov.uk'],
    ['local.tunbridge-wells.2018-05-03', 'democracy.tunbridgewells.gov.uk'],
    ['local.wakefield.2018-05-03', 'mg.wakefield.gov.uk'],
    ['local.west-lancashire.2018-05-03', 'democracy.westlancs.gov.uk'],
    ['local.wigan.2018-05-03', 'democracy.wigan.gov.uk'],
    ['local.wirral.2018-05-03', 'democracy.wirral.gov.uk'],


    ['local.waltham-forest.2018-05-03', 'democracy.walthamforest.gov.uk'],
]

# data = [
#     ['local.kirklees.2017-10-26', 'democracy.kirklees.gov.uk']
# ]

class Command(BaseCommand):
    # def add_arguments(self, parser):
    #     parser.add_argument(
    #         '--url',
    #         action='store',
    #         required=True
    #     )
    #     parser.add_argument(
    #         '--election_id',
    #         action='store',
    #         required=True
    #     )

    def handle(self, **options):
        id_to_url = {}
        path = os.path.join(
            os.path.dirname(resultsbot.__file__),
            'election_id_to_url.csv'
        )
        with open(path) as f:
            csv_file = csv.reader(f)
            for line in csv_file:
                id_to_url[line[0]] = line[1]

        for election_id, url in data:
            if election_id in id_to_url.keys():
                continue
            print(election_id)
            matcher = ModGovElectionMatcher(
                base_domain=url,
                election_id=election_id,
            )
            try:
                matcher.find_elections()
                election = matcher.match_to_election()
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print("Error on {} ({})".format(election_id, e))
                continue
            if election:
                # print("This is the URL for the given election")
                print("{},{}".format(election_id, election.url))
                with open(path, 'a') as f:
                    f.write("\n{},{}".format(election_id, election.url))

            else:
                print("No URL found for {}!".format(
                    election_id,
                ))
                print("\tHighest ID was {}".format(matcher.lookahead))
                print("\tTry the following for debugging:")
                print("\t"+matcher.format_elections_html_url())
                print("\t"+matcher.format_elections_api_url())
            # import ipdb; ipdb.set_trace()
