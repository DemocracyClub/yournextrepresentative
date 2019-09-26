import csv
import os

from django.core.management.base import BaseCommand

import resultsbot
from resultsbot.importers.modgov import ModGovElectionMatcher

data = [
    ("local.ashford.2019-05-02", "ashford.moderngov.co.uk"),
    ("local.babergh.2019-05-02", "baberghmidsuffolk.moderngov.co.uk"),
    ("local.mid-suffolk.2019-05-02", "baberghmidsuffolk.moderngov.co.uk"),
    ("local.barnsley.2019-05-02", "barnsleymbc.moderngov.co.uk"),
    ("local.brentwood.2019-05-02", "brentwood.moderngov.co.uk"),
    ("local.sevenoaks.2019-05-02", "cds.sevenoaks.gov.uk"),
    ("local.central-bedfordshire.2019-05-02", "centralbeds.moderngov.co.uk"),
    ("local.chesterfield.2019-05-02", "chesterfield.moderngov.co.uk"),
    ("local.chichester.2019-05-02", "chichester.moderngov.co.uk"),
    (
        "local.cheshire-west-and-chester.2019-05-02",
        "cmttpublic.cheshirewestandchester.gov.uk",
    ),
    ("local.worcester.2019-05-02", "committee.cityofworcester.gov.uk"),
    ("local.nottingham.2019-05-02", "committee.nottinghamcity.gov.uk"),
    ("local.lancaster.2019-05-02", "committeeadmin.lancaster.gov.uk"),
    ("local.dartford.2019-05-02", "committeedmz.dartford.gov.uk"),
    ("local.exeter.2019-05-02", "committees.exeter.gov.uk"),
    ("local.copeland.2019-05-02", "copeland.moderngov.co.uk"),
    ("local.wealden.2019-05-02", "council.wealden.gov.uk"),
    ("local.halton.2019-05-02", "councillors.halton.gov.uk"),
    ("local.herefordshire.2019-05-02", "councillors.herefordshire.gov.uk"),
    ("local.knowsley.2019-05-02", "councillors.knowsley.gov.uk"),
    ("local.liverpool.2019-05-02", "councillors.liverpool.gov.uk"),
    ("local.lewisham.2019-05-02", "councilmeetings.lewisham.gov.uk"),
    ("local.west-berkshire.2019-05-02", "decisionmaking.westberks.gov.uk"),
    ("local.blackpool.2019-05-02", "democracy.blackpool.gov.uk"),
    ("local.breckland.2019-05-02", "democracy.breckland.gov.uk"),
    ("local.cambridge.2019-05-02", "democracy.cambridge.gov.uk"),
    ("local.canterbury.2019-05-02", "democracy.canterbury.gov.uk"),
    ("local.crawley.2019-05-02", "democracy.crawley.gov.uk"),
    ("local.eastbourne.2019-05-02", "democracy.eastbourne.gov.uk"),
    ("local.east-hertfordshire.2019-05-02", "democracy.eastherts.gov.uk"),
    ("local.gateshead.2019-05-02", "democracy.gateshead.gov.uk"),
    ("local.hambleton.2019-05-02", "democracy.hambleton.gov.uk"),
    ("local.kirklees.2019-05-02", "democracy.kirklees.gov.uk"),
    ("local.leeds.2019-05-02", "democracy.leeds.gov.uk"),
    ("local.lewes.2019-05-02", "democracy.lewes-eastbourne.gov.uk"),
    ("local.newcastle-upon-tyne.2019-05-02", "democracy.newcastle.gov.uk"),
    ("local.peterborough.2019-05-02", "democracy.peterborough.gov.uk"),
    ("local.plymouth.2019-05-02", "democracy.plymouth.gov.uk"),
    ("local.portsmouth.2019-05-02", "democracy.portsmouth.gov.uk"),
    ("local.rochdale.2019-05-02", "democracy.rochdale.gov.uk"),
    ("local.ryedale.2019-05-02", "democracy.ryedale.gov.uk"),
    ("local.scarborough.2019-05-02", "democracy.scarborough.gov.uk"),
    ("local.sheffield.2019-05-02", "democracy.sheffield.gov.uk"),
    ("local.southend-on-sea.2019-05-02", "democracy.southend.gov.uk"),
    ("local.south-lakeland.2019-05-02", "democracy.southlakeland.gov.uk"),
    ("local.spelthorne.2019-05-02", "democracy.spelthorne.gov.uk"),
    ("local.stevenage.2019-05-02", "democracy.stevenage.gov.uk"),
    ("local.stockport.2019-05-02", "democracy.stockport.gov.uk"),
    ("local.tamworth.2019-05-02", "democracy.tamworth.gov.uk"),
    ("local.thanet.2019-05-02", "democracy.thanet.gov.uk"),
    ("local.tunbridge-wells.2019-05-02", "democracy.tunbridgewells.gov.uk"),
    (
        "local.kings-lynn-and-west-norfolk.2019-05-02",
        "democracy.west-norfolk.gov.uk",
    ),
    ("local.wigan.2019-05-02", "democracy.wigan.gov.uk"),
    ("local.wirral.2019-05-02", "democracy.wirral.gov.uk"),
    ("local.york.2019-05-02", "democracy.york.gov.uk"),
    ("local.bracknell-forest.2019-05-02", "democratic.bracknell-forest.gov.uk"),
    ("local.city-of-lincoln.2019-05-02", "democratic.lincoln.gov.uk"),
    ("local.south-oxfordshire.2019-05-02", "democratic.southoxon.gov.uk"),
    ("local.vale-of-white-horse.2019-05-02", "democratic.whitehorsedc.gov.uk"),
    ("local.east-hampshire.2019-05-02", "easthants.moderngov.co.uk"),
    ("local.solihull.2019-05-02", "eservices.solihull.gov.ukmginternet"),
    ("local.gloucestershire.2019-05-02", "glostext.gloucestershire.gov.uk"),
    ("local.havant.2019-05-02", "havant.moderngov.co.uk"),
    ("local.horsham.2019-05-02", "horsham.moderngov.co.uk"),
    ("local.forest-of-dean.2019-05-02", "meetings.fdean.gov.uk"),
    ("local.wakefield.2019-05-02", "mg.wakefield.gov.uk"),
    ("local.wychavon.2019-05-02", "mgov.wychavon.gov.uk"),
    ("local.mid-sussex.2019-05-02", "midsussex.moderngov.co.uk"),
    ("local.north-west-leicestershire.2019-05-02", "minutes-1.nwleics.gov.uk"),
    ("local.tewkesbury.2019-05-02", "minutes.tewkesbury.gov.uk"),
    ("local.boston.2019-05-02", "moderngov.boston.gov.uk"),
    ("local.cheshire-east.2019-05-02", "moderngov.cheshireeast.gov.uk"),
    ("local.erewash.2019-05-02", "moderngov.erewash.gov.uk"),
    ("local.harlow.2019-05-02", "moderngov.harlow.gov.uk"),
    (
        "local.hinckley-and-bosworth.2019-05-02",
        "moderngov.hinckley-bosworth.gov.uk",
    ),
    ("local.malvern-hills.2019-05-02", "moderngov.malvernhills.gov.uk"),
    (
        "local.newcastle-under-lyme.2019-05-02",
        "moderngov.newcastle-staffs.gov.uk",
    ),
    ("local.oadby-and-wigston.2019-05-02", "moderngov.oadby-wigston.gov.uk"),
    ("local.south-kesteven.2019-05-02", "moderngov.southkesteven.gov.uk"),
    ("local.st-helens.2019-05-02", "moderngov.sthelens.gov.uk"),
    ("local.bromsgrove.2019-05-02", "moderngovwebpublic.bromsgrove.gov.uk"),
    ("local.redditch.2019-05-02", "moderngovwebpublic.redditchbc.gov.uk"),
    ("local.cherwell.2019-05-02", "modgov.cherwell.gov.uk"),
    ("local.sefton.2019-05-02", "modgov.sefton.gov.uk"),
    ("local.elmbridge.2019-05-02", "mygov.elmbridge.gov.uk"),
    ("local.brighton-and-hove.2019-05-02", "present.brighton-hove.gov.uk"),
    ("local.preston.2019-05-02", "preston.moderngov.co.uk"),
    ("local.windsor-and-maidenhead.2019-05-02", "rbwm.moderngov.co.uk"),
    ("local.epping-forest.2019-05-02", "rds.eppingforestdc.gov.uk"),
    ("local.rutland.2019-05-02", "rutlandcounty.moderngov.co.uk"),
    ("local.swale.2019-05-02", "services.swale.gov.uk"),
    ("local.south-ribble.2019-05-02", "southribble.moderngov.co.uk"),
    ("local.st-albans.2019-05-02", "stalbans.moderngov.co.uk"),
    ("local.surrey-heath.2019-05-02", "surreyheath.moderngov.co.uk"),
    ("local.tameside.2019-05-02", "tameside.moderngov.co.uk"),
    ("local.tendring.2019-05-02", "tdcdemocracy.tendringdc.gov.uk"),
    ("local.blaby.2019-05-02", "w3.blaby.gov.ukdecision-making"),
    ("local.watford.2019-05-02", "watford.moderngov.co.uk"),
    ("local.wokingham.2019-05-02", "wokingham.moderngov.co.uk"),
    ("local.wolverhampton.2019-05-02", "wolverhampton.moderngov.co.uk"),
    ("local.leicester.2019-05-02", "www.cabinet.leicester.gov.uk"),
    ("local.bedford.2019-05-02", "www.councillorsupport.bedford.gov.uk"),
    (
        "local.folkestone-hythe.2019-05-02",
        "www.folkestone-hythe.gov.ukmoderngov",
    ),
    ("local.stoke-on-trent.2019-05-02", "www.moderngov.stoke.gov.uk"),
    ("local.slough.2019-05-02", "www.slough.gov.ukmoderngov"),
    ("local.bradford.2019-05-02", "bradford.moderngov.co.uk"),
    ("local.burnley.2019-05-02", "burnley.moderngov.co.uk"),
    ("local.charnwood.2019-05-02", "charnwood.moderngov.co.uk"),
    ("local.south-gloucestershire.2019-05-02", "council.southglos.gov.uk"),
    ("local.bury.2019-05-02", "councildecisions.bury.gov.uk"),
    ("local.cumbria.2019-05-02", "councilportal.cumbria.gov.uk"),
    ("local.allerdale.2019-05-02", "democracy.allerdale.gov.uk"),
    ("local.ashfield.2019-05-02", "democracy.ashfield-dc.gov.uk"),
    ("local.barrow-in-furness.2019-05-02", "democracy.barrowbc.gov.uk"),
    ("local.basingstoke-and-deane.2019-05-02", "democracy.basingstoke.gov.uk"),
    (
        "local.bath-and-north-east-somerset.2019-05-02",
        "democracy.bathnes.gov.uk",
    ),
    ("local.blackburn-with-darwen.2019-05-02", "democracy.blackburn.gov.uk"),
    ("local.chorley.2019-05-02", "democracy.chorley.gov.uk"),
    ("local.dacorum.2019-05-02", "democracy.dacorum.gov.uk"),
    ("local.darlington.2019-05-02", "democracy.darlington.gov.uk"),
    ("local.county-durham.2019-05-02", "democracy.durham.gov.uk"),
    ("local.east-lindsey.2019-05-02", "democracy.e-lindsey.gov.uk"),
    ("local.eden.2019-05-02", "democracy.eden.gov.uk"),
    ("local.epsom-and-ewell.2019-05-02", "democracy.epsom-ewell.gov.uk"),
    ("local.gedling.2019-05-02", "democracy.gedling.gov.uk"),
    ("local.gravesham.2019-05-02", "democracy.gravesham.gov.uk"),
    ("local.high-peak.2019-05-02", "democracy.highpeak.gov.uk"),
    ("local.hyndburn.2019-05-02", "democracy.hyndburnbc.gov.uk"),
    ("local.ipswich.2019-05-02", "democracy.ipswich.gov.uk"),
    ("local.kent.2019-05-02", "democracy.kent.gov.uk"),
    ("local.lichfield.2019-05-02", "democracy.lichfielddc.gov.uk"),
    ("local.maldon.2019-05-02", "democracy.maldon.gov.uk"),
    ("local.manchester.2019-05-02", "democracy.manchester.gov.uk"),
    ("local.medway.2019-05-02", "democracy.medway.gov.uk"),
    ("local.mid-devon.2019-05-02", "democracy.middevon.gov.uk"),
    ("local.north-kesteven.2019-05-02", "democracy.n-kesteven.gov.uk"),
    ("local.new-forest.2019-05-02", "democracy.newforest.gov.uk"),
    ("local.north-hertfordshire.2019-05-02", "democracy.north-herts.gov.uk"),
    ("local.north-devon.2019-05-02", "democracy.northdevon.gov.uk"),
    ("local.rushcliffe.2019-05-02", "democracy.rushcliffe.gov.uk"),
    ("local.rushmoor.2019-05-02", "democracy.rushmoor.gov.uk"),
    ("local.selby.2019-05-02", "democracy.selby.gov.uk"),
    ("local.south-holland.2019-05-02", "democracy.sholland.gov.uk"),
    (
        "local.staffordshire-moorlands.2019-05-02",
        "democracy.staffsmoorlands.gov.uk",
    ),
    ("local.stratford-on-avon.2019-05-02", "democracy.stratford.gov.uk"),
    ("local.thurrock.2019-05-02", "democracy.thurrock.gov.uk"),
    ("local.tonbridge-and-malling.2019-05-02", "democracy.tmbc.gov.uk"),
    ("local.torridge.2019-05-02", "democracy.torridge.gov.uk"),
    ("local.west-lindsey.2019-05-02", "democracy.west-lindsey.gov.uk"),
    ("local.west-lancashire.2019-05-02", "democracy.westlancs.gov.uk"),
    ("local.swindon.2019-05-02", "democracy.winchester.gov.uk"),
    ("local.winchester.2019-05-02", "democracy.winchester.gov.uk"),
    ("local.trafford.2019-05-02", "democratic.trafford.gov.uk"),
    ("local.eastleigh.2019-05-02", "meetings.eastleigh.gov.uk"),
    ("local.maidstone.2019-05-02", "meetings.maidstone.gov.uk"),
    ("local.woking.2019-05-02", "moderngov.woking.gov.uk"),
    ("local.waverley.2019-05-02", "modgov.waverley.gov.uk"),
    ("local.surrey.2019-05-02", "mycouncil.surreycc.gov.uk"),
    (
        "local.reigate-and-banstead.2019-05-02",
        "reigate-banstead.moderngov.co.uk",
    ),
    ("local.salford.2019-05-02", "sccdemocracy.salford.gov.uk"),
    ("local.uttlesford.2019-05-02", "uttlesford.moderngov.co.uk"),
    ("local.west-sussex.2019-05-02", "westsussex.moderngov.co.uk"),
    ("local.basildon.2019-05-02", "www.basildonmeetings.info"),
    ("local.fenland.2019-05-02", "www.fenland.gov.uklocalgov"),
    ("local.southampton.2019-05-02", "www.southampton.gov.ukmodernGov"),
    ("local.torbay.2019-05-02", "www.torbay.gov.ukDemocraticServices"),
    ("local.guildford.2019-05-02", "www2.guildford.gov.ukcouncilmeetings"),
    ("local.hertsmere.2019-05-02", "www5.hertsmere.gov.ukdemocracy"),
    ("local.wyre.2019-05-02", "wyre.moderngov.co.uk"),
]


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
            os.path.dirname(resultsbot.__file__), "election_id_to_url.csv"
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
                base_domain=url, election_id=election_id
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
                with open(path, "a") as f:
                    f.write("\n{},{}".format(election_id, election.url))

            else:
                print("No URL found for {}!".format(election_id))
                print("\tHighest ID was {}".format(matcher.lookahead))
                print("\tTry the following for debugging:")
                print("\t" + matcher.format_elections_html_url())
                print("\t" + matcher.format_elections_api_url())
