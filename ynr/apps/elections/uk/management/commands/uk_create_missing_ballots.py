import requests
from django.core.management.base import BaseCommand
from django.db import transaction

from candidates.models import Ballot
from elections.uk.every_election import EEElection

data = """local.southwark.2018-05-03	LBW:london-bridge-and-west-bermondsey	https://elections.democracyclub.org.uk/elections/local.southwark.london-bridge-west-bermondsey.2018-05-03/
local.brent.2018-05-03	LBW:E05000105	https://elections.democracyclub.org.uk/elections/local.brent.willesden-green.2018-05-03/
local.cherwell.2018-05-03	DIW:E05010928	https://elections.democracyclub.org.uk/elections/local.cherwell.bicester-west.2018-05-03/
local.stockport.2018-05-03	MTW:E05000788	https://elections.democracyclub.org.uk/elections/local.stockport.edgeley-and-cheadle-heath.2018-05-03/
local.tamworth.2018-05-03	DIW:E05007070	https://elections.democracyclub.org.uk/elections/local.tamworth.glascote.2018-05-03/
parl.2010-05-06	65686	https://elections.democracyclub.org.uk/elections/parl.thirsk-and-malton.2010-05-06/
local.rushmoor.2016-05-05	DIW:E05008989	https://elections.democracyclub.org.uk/elections/local.rushmoor.aldershot-park.2016-05-05/
local.glasgow.2016-05-05	UTW:S13002650	https://elections.democracyclub.org.uk/elections/local.glasgow-city.anderstoncity.by.2016-05-05/
local.wigan.2018-02-22	MTW:E05000846	https://elections.democracyclub.org.uk/elections/local.wigan.bryn.2018-02-22/
local.hartlepool.2016-05-05	UTW:E05008944	https://elections.democracyclub.org.uk/elections/local.hartlepool.fens-and-rossmere.2016-05-05/
local.hartlepool.2016-05-05	UTW:E05008945	https://elections.democracyclub.org.uk/elections/local.hartlepool.foggy-furze.2016-05-05/
local.hartlepool.2016-05-05	UTW:E05008946	https://elections.democracyclub.org.uk/elections/local.hartlepool.hart.2016-05-05/
local.hartlepool.2016-05-05	UTW:E05008948	https://elections.democracyclub.org.uk/elections/local.hartlepool.jesmond.2016-05-05/
local.hartlepool.2016-05-05	UTW:E05008949	https://elections.democracyclub.org.uk/elections/local.hartlepool.manor-house.2016-05-05/
local.hartlepool.2016-05-05	UTW:E05008950	https://elections.democracyclub.org.uk/elections/local.hartlepool.rural-west.2016-05-05/
local.hartlepool.2016-05-05	UTW:E05008951	https://elections.democracyclub.org.uk/elections/local.hartlepool.seaton.2016-05-05/
local.milton-keynes.2016-05-05	NODATA:E06000042-campbell-park-and-old-woughton	https://elections.democracyclub.org.uk/elections/local.milton-keynes.campbell-park-old-woughton.2016-05-05/
local.milton-keynes.2016-05-05	NODATA:E06000042-newport-pagnell-north-and-hanslope	https://elections.democracyclub.org.uk/elections/local.milton-keynes.newport-pagnell-north-hanslope.2016-05-05/
local.milton-keynes.2016-05-05	NODATA:E06000042-woughton-and-fishermead	https://elections.democracyclub.org.uk/elections/local.milton-keynes.woughton-fishermead.2016-05-05/
local.milton-keynes.2016-05-05	UTW:E05009424	https://elections.democracyclub.org.uk/elections/local.milton-keynes.woughton-fishermead.2016-05-05/
local.portsmouth.2016-05-05	UTW:E05002447	https://elections.democracyclub.org.uk/elections/local.portsmouth.eastney-and-craneswater.2016-05-05/
local.southampton.2016-05-05	UTW:E05002463	https://elections.democracyclub.org.uk/elections/local.southampton.millbrook.2016-05-05/
local.southend-on-sea.2016-05-05	UTW:E05002212	https://elections.democracyclub.org.uk/elections/local.southend-on-sea.belfairs.2016-05-05
local.southend-on-sea.2016-05-05	UTW:E05002213	https://elections.democracyclub.org.uk/elections/local.southend-on-sea.blenheim-park.2016-05-05
local.southend-on-sea.2016-05-05	UTW:E05002214	https://elections.democracyclub.org.uk/elections/local.southend-on-sea.chalkwell.2016-05-05
local.southend-on-sea.2016-05-05	UTW:E05002215	https://elections.democracyclub.org.uk/elections/local.southend-on-sea.eastwood-park.2016-05-05
local.southend-on-sea.2016-05-05	UTW:E05002216	https://elections.democracyclub.org.uk/elections/local.southend-on-sea.kursaal.2016-05-05
local.southend-on-sea.2016-05-05	UTW:E05002217	https://elections.democracyclub.org.uk/elections/local.southend-on-sea.leigh.2016-05-05
local.southend-on-sea.2016-05-05	UTW:E05002218	https://elections.democracyclub.org.uk/elections/local.southend-on-sea.milton.2016-05-05
local.southend-on-sea.2016-05-05	UTW:E05002219	https://elections.democracyclub.org.uk/elections/local.southend-on-sea.prittlewell.2016-05-05
local.southend-on-sea.2016-05-05	UTW:E05002222	https://elections.democracyclub.org.uk/elections/local.southend-on-sea.shoeburyness.2016-05-05
local.southend-on-sea.2016-05-05	UTW:E05002223	https://elections.democracyclub.org.uk/elections/local.southend-on-sea.southchurch.2016-05-05
local.southend-on-sea.2016-05-05	UTW:E05002220	https://elections.democracyclub.org.uk/elections/local.southend-on-sea.st-laurence.2016-05-05
local.southend-on-sea.2016-05-05	UTW:E05002221	https://elections.democracyclub.org.uk/elections/local.southend-on-sea.st-lukes.2016-05-05
local.southend-on-sea.2016-05-05	UTW:E05002224	https://elections.democracyclub.org.uk/elections/local.southend-on-sea.thorpe.2016-05-05
local.southend-on-sea.2016-05-05	UTW:E05002225	https://elections.democracyclub.org.uk/elections/local.southend-on-sea.victoria.2016-05-05
local.southend-on-sea.2016-05-05	UTW:E05002227	https://elections.democracyclub.org.uk/elections/local.southend-on-sea.west-leigh.2016-05-05
local.southend-on-sea.2016-05-05	UTW:E05002228	https://elections.democracyclub.org.uk/elections/local.southend-on-sea.west-shoebury.2016-05-05
local.southend-on-sea.2016-05-05	UTW:E05002226	https://elections.democracyclub.org.uk/elections/local.southend-on-sea.westborough.2016-05-05
local.swindon.2016-05-05	UTW:E05008967	https://elections.democracyclub.org.uk/elections/local.swindon.rodbourne-cheney.2016-05-05/
local.thurrock.2016-05-05	UTW:E05002230	https://elections.democracyclub.org.uk/elections/local.thurrock.belhus.2016-05-05
local.thurrock.2016-05-05	UTW:E05002233	https://elections.democracyclub.org.uk/elections/local.thurrock.corringham-and-fobbing.2016-05-05
local.thurrock.2016-05-05	UTW:E05002234	https://elections.democracyclub.org.uk/elections/local.thurrock.east-tilbury.2016-05-05
local.thurrock.2016-05-05	UTW:E05002235	https://elections.democracyclub.org.uk/elections/local.thurrock.grays-riverside.2016-05-05
local.thurrock.2016-05-05	UTW:E05002236	https://elections.democracyclub.org.uk/elections/local.thurrock.grays-thurrock.2016-05-05
local.thurrock.2016-05-05	UTW:E05002237	https://elections.democracyclub.org.uk/elections/local.thurrock.little-thurrock-blackshots.2016-05-05
local.thurrock.2016-05-05	UTW:E05002241	https://elections.democracyclub.org.uk/elections/local.thurrock.south-chafford.2016-05-05
local.thurrock.2016-05-05	UTW:E05002242	https://elections.democracyclub.org.uk/elections/local.thurrock.stanford-east-and-corringham-town.2016-05-05
local.thurrock.2016-05-05	UTW:E05002243	https://elections.democracyclub.org.uk/elections/local.thurrock.stanford-le-hope-west.2016-05-05
local.thurrock.2016-05-05	UTW:E05002245	https://elections.democracyclub.org.uk/elections/local.thurrock.the-homesteads.2016-05-05
local.thurrock.2016-05-05	UTW:E05002247	https://elections.democracyclub.org.uk/elections/local.thurrock.tilbury-st-chads.2016-05-05
local.thurrock.2016-05-05	UTW:E05002248	https://elections.democracyclub.org.uk/elections/local.thurrock.west-thurrock-and-south-stifford.2016-05-05
local.warrington.2016-05-05	UTW:E05001598	https://elections.democracyclub.org.uk/elections/local.warrington.appleton.2016-05-05/
local.warrington.2016-05-05	UTW:E05001603	https://elections.democracyclub.org.uk/elections/local.warrington.fairfield-howley.2016-05-05/
local.warrington.2016-05-05	UTW:E05001599	https://elections.democracyclub.org.uk/elections/local.warrington.bewsey-whitecross.2016-05-05/
local.warrington.2016-05-05	UTW:E05001600	https://elections.democracyclub.org.uk/elections/local.warrington.birchwood.2016-05-05/
local.warrington.2016-05-05	NODATA:E06000007-chapelford-and-old-hall	https://elections.democracyclub.org.uk/elections/local.warrington.chapelford-old-hall.2016-05-05/
local.warrington.2016-05-05	UTW:E05011028	https://elections.democracyclub.org.uk/elections/local.warrington.chapelford-old-hall.2016-05-05/
local.warrington.2016-05-05	UTW:E05011031	https://elections.democracyclub.org.uk/elections/local.warrington.grappenhall.2016-05-05/
local.warrington.2016-05-05	NODATA:E06000007-great-sankey-north-and-whittle-hall	https://elections.democracyclub.org.uk/elections/local.warrington.great-sankey-north-whittle-hall.2016-05-05/
local.warrington.2016-05-05	UTW:E05011032	https://elections.democracyclub.org.uk/elections/local.warrington.great-sankey-north-whittle-hall.2016-05-05/
local.warrington.2016-05-05	NODATA:E06000007-lymm-north-and-thelwall	https://elections.democracyclub.org.uk/elections/local.warrington.lymm-north-thelwall.2016-05-05/
local.warrington.2016-05-05	UTW:E05011036	https://elections.democracyclub.org.uk/elections/local.warrington.lymm-north-thelwall.2016-05-05/
local.warrington.2016-05-05	NODATA:E06000007-lymm-south	https://elections.democracyclub.org.uk/elections/local.warrington.lymm-south.2016-05-05/
local.warrington.2016-05-05	NODATA:E06000007-grappenhall	https://elections.democracyclub.org.uk/elections/local.warrington.grappenhall.2016-05-05/
local.warrington.2016-05-05	UTW:E05001606	https://elections.democracyclub.org.uk/elections/local.warrington.great-sankey-south.2016-05-05/
parl.2016-05-05	66107	https://elections.democracyclub.org.uk/elections/parl.ogmore.by.2016-05-05/
parl.bridgend.ogmore.2016-05-05	66107	https://elections.democracyclub.org.uk/elections/parl.ogmore.by.2016-05-05/"""


class Command(BaseCommand):
    help = "Create posts and elections from a EveryElection"

    def get_ballot_and_parent_from_ee_url(self, url):
        api_url = url.replace("/elections/", "/api/elections/")
        ballot_dict = requests.get(api_url).json()
        parent_id = ballot_dict["group"]
        parent_url = api_url.replace(ballot_dict["election_id"], parent_id)
        parent_dict = requests.get(parent_url).json()
        return ballot_dict, parent_dict

    @transaction.atomic
    def handle(self, *args, **options):
        for row in data.splitlines():
            election_slug, post_id, ee_url = row.split("\t")
            ballot, parent = self.get_ballot_and_parent_from_ee_url(ee_url)
            importer = EEElection(ballot)
            ballot, created = importer.get_or_create_ballot(EEElection(parent))
            ballot.post.postidentifier_set.get_or_create(identifier=post_id)
