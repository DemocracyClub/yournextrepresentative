from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Prefetch, Count
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views import View
from django.views.generic import UpdateView
from django.views.decorators.cache import cache_control
from django.views.generic import DetailView, TemplateView
from slugify import slugify

from auth_helpers.views import GroupRequiredMixin
from candidates.csv_helpers import memberships_dicts_for_csv, list_to_csv
from candidates.forms import ToggleLockForm
from candidates.models import (
    PostExtraElection,
    get_edits_allowed,
    TRUSTED_TO_LOCK_GROUP_NAME,
    LoggedAction,
)
from candidates.models.auth import is_post_locked
from candidates.views import get_client_ip
from candidates.views.helpers import (
    get_max_winners,
    get_person_form_fields,
    group_candidates_by_party,
    split_by_elected,
    split_candidacies,
)
from elections.mixins import ElectionMixin
from elections.models import Election
from moderation_queue.forms import SuggestedPostLockForm
from moderation_queue.models import SuggestedPostLock
from official_documents.models import OfficialDocument
from people.forms import NewPersonForm, PersonIdentifierFormsetFactory
from popolo.models import Membership, Post

from .filters import BallotFilter, filter_shortcuts


class ElectionView(DetailView):
    template_name = "elections/election_detail.html"
    model = Election
    slug_url_kwarg = "election"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ballots"] = (
            PostExtraElection.objects.filter(election=self.object)
            .order_by("post__label")
            .select_related("post")
            .select_related("election")
            .select_related("resultset")
            .prefetch_related("suggestedpostlock_set")
            .prefetch_related(
                Prefetch(
                    "membership_set",
                    Membership.objects.select_related("party", "person"),
                )
            )
        )

        return context


class ElectionListView(TemplateView):
    template_name = "elections/election_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        qs = (
            PostExtraElection.objects.filter(election__current=True)
            .select_related("election", "post")
            .prefetch_related("suggestedpostlock_set")
            .annotate(memberships_count=Count("membership"))
            .order_by("election__election_date", "election__name")
        )

        f = BallotFilter(self.request.GET, qs)
        context["filter"] = f
        context["shortcuts"] = filter_shortcuts(self.request)
        return context


class UnlockedBallotsForElectionListView(ElectionMixin, TemplateView):
    template_name = "elections/unlocked_ballots_for_election_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_constituencies = 0
        total_locked = 0
        keys = ("locked", "unlocked")
        for k in keys:
            context[k] = []
        postextraelections = (
            PostExtraElection.objects.filter(election=self.election_data)
            .select_related("post")
            .all()
        )
        for postextraelection in postextraelections:
            total_constituencies += 1
            if postextraelection.candidates_locked:
                context_field = "locked"
                total_locked += 1
            else:
                context_field = "unlocked"
            context[context_field].append(
                {
                    "id": postextraelection.post.slug,
                    "name": postextraelection.post.short_label,
                    "ballot": postextraelection,
                }
            )
        for k in keys:
            context[k].sort(key=lambda c: c["name"])
        context["total_constituencies"] = total_constituencies
        context["total_left"] = total_constituencies - total_locked
        if total_constituencies > 0:
            context["percent_done"] = (
                100 * total_locked
            ) // total_constituencies
        else:
            context["percent_done"] = 0
        return context


class BallotPaperView(TemplateView):
    template_name = "elections/ballot_view.html"

    @method_decorator(cache_control(max_age=(60 * 20)))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        from candidates.election_specific import shorten_post_label

        context = super().get_context_data(**kwargs)

        context["post_election"] = get_object_or_404(
            PostExtraElection.objects.all().select_related("post", "election"),
            ballot_paper_id=context["election"],
        )

        mp_post = context["post_election"].post
        context["election"] = election = context["post_election"].election
        context["post_id"] = post_id = mp_post.slug
        context["post_obj"] = mp_post

        documents_by_type = {}
        # Make sure that every available document type has a key in
        # the dictionary, even if there are no such documents.
        doc_lookup = {
            t[0]: (t[1], t[2]) for t in OfficialDocument.DOCUMENT_TYPES
        }
        for t in doc_lookup.values():
            documents_by_type[t] = []
        documents_for_post = OfficialDocument.objects.filter(
            post_election=context["post_election"]
        )
        for od in documents_for_post:
            documents_by_type[doc_lookup[od.document_type]].append(od)
        context["official_documents"] = documents_by_type.items()
        context["some_official_documents"] = documents_for_post.count()

        context["post_label"] = mp_post.label
        context["post_label_shorter"] = shorten_post_label(
            context["post_label"]
        )

        context["redirect_after_login"] = context[
            "post_election"
        ].get_absolute_url()

        context["post_data"] = {"id": mp_post.slug, "label": mp_post.label}

        pee = context["post_election"]

        context["candidates_locked"] = pee.candidates_locked

        context["has_lock_suggestion"] = SuggestedPostLock.objects.filter(
            postextraelection=pee
        ).exists()

        if self.request.user.is_authenticated:
            context[
                "current_user_suggested_lock"
            ] = SuggestedPostLock.objects.filter(
                user=self.request.user, postextraelection=pee
            ).exists()

        context["suggest_lock_form"] = SuggestedPostLockForm(
            initial={"postextraelection": pee}
        )

        if self.request.user.is_authenticated:
            context[
                "user_has_suggested_lock"
            ] = SuggestedPostLock.objects.filter(
                user=self.request.user, postextraelection=pee
            ).exists()

        context["lock_form"] = ToggleLockForm(
            initial={
                "post_id": post_id,
                "lock": not context["candidates_locked"],
            }
        )

        context["candidate_list_edits_allowed"] = get_edits_allowed(
            self.request.user, context["candidates_locked"]
        )

        extra_qs = Membership.objects.select_related("post_election__election")
        current_candidacies, past_candidacies = split_candidacies(
            election,
            mp_post.memberships.select_related("person", "party").all(),
        )

        area_2015_map = {
            "WMC:E14000824": "65693",
            "WMC:E14000825": "65633",
            "WMC:E14000826": "65735",
            "WMC:E14000827": "65556",
            "WMC:E14000820": "65657",
            "WMC:E14000821": "65953",
            "WMC:E14000822": "66076",
            "WMC:E14000823": "66038",
            "WMC:E14000828": "65815",
            "WMC:E14000829": "65696",
            "WMC:E14000948": "65829",
            "WMC:E14000543": "66006",
            "WMC:E14000810": "65647",
            "WMC:E14000813": "65718",
            "WMC:E14000540": "65662",
            "WMC:E14000699": "65857",
            "WMC:E14000751": "66069",
            "WMC:E14000546": "65711",
            "WMC:S14000048": "14445",
            "WMC:S14000049": "14446",
            "WMC:E14000912": "65889",
            "WMC:E14000913": "65891",
            "WMC:E14000914": "66027",
            "WMC:E14000915": "65763",
            "WMC:E14000916": "65706",
            "WMC:E14000917": "65842",
            "WMC:S14000040": "14436",
            "WMC:S14000041": "14437",
            "WMC:S14000042": "14438",
            "WMC:S14000043": "14439",
            "WMC:S14000044": "14440",
            "WMC:S14000045": "14441",
            "WMC:S14000046": "14442",
            "WMC:S14000047": "14443",
            "WMC:E14000727": "65576",
            "WMC:E14000726": "65836",
            "WMC:E14000725": "65915",
            "WMC:E14000724": "65671",
            "WMC:E14000723": "65599",
            "WMC:E14000649": "65636",
            "WMC:E14000721": "65752",
            "WMC:E14000720": "65550",
            "WMC:E14000644": "65926",
            "WMC:E14000645": "65835",
            "WMC:E14000646": "65771",
            "WMC:E14000690": "65816",
            "WMC:E14000640": "65734",
            "WMC:W07000063": "66111",
            "WMC:E14000642": "66030",
            "WMC:E14000643": "66057",
            "WMC:E14001034": "65629",
            "WMC:E14001035": "65758",
            "WMC:E14001036": "65851",
            "WMC:E14001037": "65963",
            "WMC:E14001030": "66047",
            "WMC:E14001031": "65716",
            "WMC:E14001032": "66058",
            "WMC:E14001033": "65873",
            "WMC:E14000544": "65898",
            "WMC:E14001038": "65742",
            "WMC:E14001039": "65612",
            "WMC:E14000965": "66067",
            "WMC:E14000964": "65854",
            "WMC:E14000967": "65960",
            "WMC:E14000966": "65907",
            "WMC:S14000039": "14435",
            "WMC:S14000038": "14434",
            "WMC:E14000963": "65732",
            "WMC:E14000962": "66073",
            "WMC:S14000035": "14431",
            "WMC:S14000034": "14430",
            "WMC:S14000037": "14433",
            "WMC:S14000036": "14432",
            "WMC:E14000969": "65606",
            "WMC:E14000968": "65571",
            "WMC:S14000033": "14429",
            "WMC:S14000032": "14428",
            "WMC:E14000639": "65759",
            "WMC:E14000731": "65650",
            "WMC:W07000072": "66093",
            "WMC:E14000868": "65663",
            "WMC:E14000869": "65653",
            "WMC:W07000077": "66097",
            "WMC:W07000049": "66101",
            "WMC:E14000860": "65822",
            "WMC:E14000861": "66059",
            "WMC:E14000862": "65910",
            "WMC:E14000863": "65768",
            "WMC:E14000864": "65634",
            "WMC:E14000865": "65559",
            "WMC:E14000866": "65643",
            "WMC:E14000867": "65945",
            "WMC:W07000062": "66121",
            "WMC:E14000631": "65801",
            "WMC:N06000006": "66129",
            "WMC:N06000007": "66130",
            "WMC:W07000066": "66109",
            "WMC:N06000001": "66124",
            "WMC:N06000002": "66125",
            "WMC:N06000003": "66126",
            "WMC:W07000068": "66088",
            "WMC:W07000069": "66082",
            "WMC:N06000008": "66131",
            "WMC:N06000009": "66132",
            "WMC:E14000819": "65998",
            "WMC:E14000818": "65888",
            "WMC:E14000549": "65731",
            "WMC:E14000548": "65751",
            "WMC:E14000547": "65798",
            "WMC:E14000814": "66007",
            "WMC:E14000545": "65623",
            "WMC:E14000816": "65949",
            "WMC:E14000811": "65772",
            "WMC:E14000542": "66012",
            "WMC:E14000541": "65665",
            "WMC:E14000812": "65932",
            "WMC:E14000600": "66009",
            "WMC:E14000601": "66031",
            "WMC:E14000602": "65574",
            "WMC:E14000603": "65852",
            "WMC:E14000604": "65954",
            "WMC:E14000605": "65617",
            "WMC:E14000606": "65639",
            "WMC:E14000607": "65849",
            "WMC:E14000608": "65909",
            "WMC:E14000609": "65846",
            "WMC:E14000929": "65920",
            "WMC:E14000928": "65986",
            "WMC:E14000921": "65601",
            "WMC:E14000920": "65793",
            "WMC:E14000923": "65549",
            "WMC:E14000654": "65603",
            "WMC:E14000925": "65959",
            "WMC:E14000924": "65632",
            "WMC:E14000927": "65610",
            "WMC:E14000926": "65563",
            "WMC:E14000778": "65941",
            "WMC:E14000779": "65866",
            "WMC:E14000774": "66053",
            "WMC:E14000775": "65869",
            "WMC:E14000776": "65568",
            "WMC:E14000777": "65765",
            "WMC:E14000770": "65778",
            "WMC:E14000771": "65709",
            "WMC:E14000772": "65618",
            "WMC:E14000773": "65984",
            "WMC:E14000675": "65701",
            "WMC:E14000674": "65755",
            "WMC:E14000677": "65823",
            "WMC:E14000676": "65794",
            "WMC:E14000671": "65806",
            "WMC:E14000670": "65555",
            "WMC:E14000673": "65808",
            "WMC:E14000672": "66054",
            "WMC:E14000679": "65573",
            "WMC:E14000678": "65813",
            "WMC:E14001009": "65733",
            "WMC:E14001008": "65825",
            "WMC:E14001005": "65782",
            "WMC:E14001004": "65660",
            "WMC:E14001007": "65613",
            "WMC:E14001006": "65868",
            "WMC:E14001001": "65810",
            "WMC:E14001000": "65904",
            "WMC:E14001003": "65659",
            "WMC:E14001002": "66074",
            "WMC:E14000733": "65990",
            "WMC:E14000781": "65988",
            "WMC:E14000780": "66068",
            "WMC:E14000783": "65604",
            "WMC:E14000782": "65807",
            "WMC:E14000785": "65978",
            "WMC:E14000784": "65587",
            "WMC:E14000787": "65705",
            "WMC:E14000786": "66020",
            "WMC:E14000789": "66041",
            "WMC:E14000788": "65616",
            "WMC:E14000851": "65760",
            "WMC:E14000850": "65817",
            "WMC:E14000581": "65821",
            "WMC:E14000580": "65738",
            "WMC:E14000587": "65694",
            "WMC:E14000586": "65697",
            "WMC:E14000585": "65933",
            "WMC:E14000856": "65859",
            "WMC:E14000859": "65713",
            "WMC:E14000858": "65776",
            "WMC:E14000589": "66036",
            "WMC:E14000588": "65995",
            "WMC:S14000028": "14424",
            "WMC:S14000029": "14425",
            "WMC:S14000020": "14417",
            "WMC:S14000021": "14418",
            "WMC:E14000922": "65741",
            "WMC:E14000739": "65967",
            "WMC:E14000730": "65578",
            "WMC:E14000638": "65885",
            "WMC:E14000732": "65796",
            "WMC:E14000746": "65850",
            "WMC:E14000734": "65674",
            "WMC:E14000735": "65640",
            "WMC:E14000736": "65699",
            "WMC:E14000737": "65912",
            "WMC:E14000738": "65557",
            "WMC:E14000630": "65946",
            "WMC:E14000633": "65558",
            "WMC:E14000632": "65980",
            "WMC:E14000635": "65940",
            "WMC:E14000634": "65721",
            "WMC:E14000637": "65792",
            "WMC:E14000636": "65886",
            "WMC:E14001041": "65921",
            "WMC:E14001040": "65827",
            "WMC:E14001043": "65847",
            "WMC:E14001042": "65552",
            "WMC:E14001045": "65831",
            "WMC:E14001044": "65897",
            "WMC:E14001047": "66039",
            "WMC:E14001046": "65622",
            "WMC:E14001049": "65777",
            "WMC:E14001048": "65774",
            "WMC:E14000910": "65654",
            "WMC:E14000911": "65688",
            "WMC:E14000976": "65609",
            "WMC:E14000977": "65648",
            "WMC:E14000974": "65770",
            "WMC:E14000975": "65950",
            "WMC:E14000972": "65710",
            "WMC:E14000973": "65783",
            "WMC:E14000970": "65641",
            "WMC:E14000971": "65908",
            "WMC:S14000026": "14423",
            "WMC:S14000027": "14444",
            "WMC:S14000024": "14421",
            "WMC:S14000025": "14422",
            "WMC:S14000022": "14419",
            "WMC:S14000023": "14420",
            "WMC:E14000978": "66042",
            "WMC:E14000979": "65911",
            "WMC:E14000745": "65994",
            "WMC:E14000744": "66003",
            "WMC:E14000747": "65814",
            "WMC:E14000830": "65862",
            "WMC:E14000741": "65754",
            "WMC:E14000740": "66018",
            "WMC:E14000743": "65582",
            "WMC:E14000742": "65786",
            "WMC:E14000749": "65724",
            "WMC:E14000748": "66052",
            "WMC:E14000918": "65698",
            "WMC:E14000919": "65957",
            "WMC:E14000895": "65722",
            "WMC:E14000894": "65579",
            "WMC:E14000897": "65843",
            "WMC:E14000896": "65598",
            "WMC:E14000891": "66032",
            "WMC:E14000890": "65982",
            "WMC:E14000893": "66005",
            "WMC:E14000892": "65700",
            "WMC:W07000057": "66108",
            "WMC:W07000056": "66099",
            "WMC:W07000055": "66094",
            "WMC:W07000054": "66084",
            "WMC:E14000899": "65584",
            "WMC:E14000898": "66043",
            "WMC:W07000051": "66120",
            "WMC:W07000050": "66090",
            "WMC:E14000648": "65590",
            "WMC:E14000722": "65971",
            "WMC:E14000558": "65611",
            "WMC:E14000559": "65581",
            "WMC:E14000808": "65834",
            "WMC:E14000809": "65819",
            "WMC:E14000806": "65661",
            "WMC:E14000807": "66048",
            "WMC:E14000804": "65936",
            "WMC:E14000553": "65689",
            "WMC:E14000554": "65726",
            "WMC:E14000803": "65901",
            "WMC:E14000556": "65934",
            "WMC:E14000801": "66080",
            "WMC:E14000647": "65893",
            "WMC:W07000059": "66100",
            "WMC:W07000058": "66085",
            "WMC:E14000641": "66021",
            "WMC:E14000729": "65875",
            "WMC:E14000728": "65675",
            "WMC:E14000949": "65848",
            "WMC:W07000053": "66104",
            "WMC:W07000052": "66092",
            "WMC:E14000758": "65899",
            "WMC:E14000652": "65781",
            "WMC:E14000938": "65684",
            "WMC:E14000939": "66051",
            "WMC:E14000932": "65812",
            "WMC:E14000933": "65962",
            "WMC:E14000930": "65680",
            "WMC:E14000931": "65879",
            "WMC:E14000936": "65788",
            "WMC:E14000937": "65997",
            "WMC:E14000934": "65922",
            "WMC:E14000935": "65762",
            "WMC:E14000709": "65870",
            "WMC:E14000708": "65900",
            "WMC:E14000701": "65655",
            "WMC:E14000700": "65764",
            "WMC:E14000703": "65938",
            "WMC:E14000702": "65865",
            "WMC:E14000705": "66064",
            "WMC:E14000704": "65779",
            "WMC:E14000707": "65952",
            "WMC:E14000706": "65955",
            "WMC:E14000666": "65746",
            "WMC:E14000667": "65553",
            "WMC:E14000664": "65799",
            "WMC:E14000665": "65723",
            "WMC:E14000662": "66070",
            "WMC:E14000663": "65863",
            "WMC:E14000660": "66025",
            "WMC:E14000661": "65924",
            "WMC:E14000668": "65621",
            "WMC:E14000669": "65672",
            "WMC:E14001018": "65916",
            "WMC:E14001019": "65608",
            "WMC:E14001016": "66079",
            "WMC:E14001017": "65874",
            "WMC:E14001014": "65631",
            "WMC:E14001015": "65638",
            "WMC:E14001012": "65832",
            "WMC:E14001013": "65651",
            "WMC:E14001010": "65635",
            "WMC:E14001011": "65890",
            "WMC:W07000061": "66096",
            "WMC:E14000989": "65992",
            "WMC:E14000988": "65767",
            "WMC:E14000987": "65964",
            "WMC:E14000986": "65880",
            "WMC:E14000985": "65703",
            "WMC:E14000984": "66040",
            "WMC:E14000983": "65747",
            "WMC:E14000982": "65586",
            "WMC:E14000981": "65607",
            "WMC:E14000980": "65858",
            "WMC:E14000815": "66061",
            "WMC:E14000792": "65704",
            "WMC:E14000793": "66066",
            "WMC:E14000790": "66013",
            "WMC:E14000791": "66046",
            "WMC:E14000796": "65766",
            "WMC:E14000797": "65785",
            "WMC:E14000794": "65970",
            "WMC:E14000795": "65644",
            "WMC:E14000798": "65987",
            "WMC:E14000799": "65690",
            "WMC:E14000598": "65787",
            "WMC:E14000599": "65839",
            "WMC:E14000594": "65685",
            "WMC:E14000595": "65620",
            "WMC:E14000596": "66000",
            "WMC:E14000597": "65844",
            "WMC:E14000590": "65670",
            "WMC:E14000591": "66065",
            "WMC:E14000592": "65595",
            "WMC:E14000593": "65958",
            "WMC:E14000842": "66063",
            "WMC:E14000843": "65676",
            "WMC:E14000840": "65745",
            "WMC:E14000841": "65855",
            "WMC:E14000846": "65619",
            "WMC:E14000847": "65642",
            "WMC:E14000844": "65729",
            "WMC:E14000845": "65840",
            "WMC:E14000848": "65872",
            "WMC:E14000849": "66017",
            "WMC:E14000817": "65999",
            "WMC:E14000561": "65667",
            "WMC:E14000560": "65931",
            "WMC:E14000563": "66072",
            "WMC:E14000562": "65597",
            "WMC:E14000565": "65966",
            "WMC:E14000564": "65989",
            "WMC:E14000567": "65804",
            "WMC:E14000566": "66028",
            "WMC:E14000569": "65820",
            "WMC:E14000568": "65707",
            "WMC:E14000961": "65591",
            "WMC:E14000960": "65715",
            "WMC:E14000628": "65797",
            "WMC:E14000629": "65818",
            "WMC:E14000622": "65914",
            "WMC:E14000623": "65749",
            "WMC:E14000620": "65929",
            "WMC:E14000621": "65972",
            "WMC:E14000626": "66075",
            "WMC:E14000627": "65727",
            "WMC:E14000624": "65748",
            "WMC:E14000625": "65615",
            "WMC:S14000031": "14427",
            "WMC:S14000030": "14426",
            "WMC:E14001052": "65577",
            "WMC:E14001053": "65625",
            "WMC:E14001050": "65593",
            "WMC:E14001051": "65948",
            "WMC:E14001056": "66010",
            "WMC:E14001057": "65695",
            "WMC:E14001054": "65757",
            "WMC:E14001055": "65562",
            "WMC:E14001058": "66078",
            "WMC:E14001059": "65669",
            "WMC:E14000943": "65951",
            "WMC:E14000942": "65902",
            "WMC:E14000941": "65666",
            "WMC:E14000940": "66034",
            "WMC:E14000947": "65800",
            "WMC:E14000946": "65614",
            "WMC:E14000945": "65943",
            "WMC:E14000944": "65719",
            "WMC:S14000013": "14410",
            "WMC:S14000012": "14409",
            "WMC:S14000011": "14408",
            "WMC:S14000010": "14407",
            "WMC:S14000017": "14414",
            "WMC:S14000016": "14413",
            "WMC:S14000015": "14412",
            "WMC:S14000014": "14411",
            "WMC:E14000756": "65624",
            "WMC:E14000757": "65592",
            "WMC:E14000754": "65947",
            "WMC:E14000755": "65691",
            "WMC:E14000752": "65883",
            "WMC:E14000753": "65717",
            "WMC:E14000750": "65824",
            "WMC:E14000698": "66033",
            "WMC:E14000697": "66062",
            "WMC:E14000696": "66023",
            "WMC:E14000695": "65743",
            "WMC:E14000694": "65803",
            "WMC:E14000693": "66044",
            "WMC:E14000692": "65567",
            "WMC:E14000691": "66050",
            "WMC:E14000759": "65630",
            "WMC:E14000886": "65637",
            "WMC:E14000887": "66045",
            "WMC:E14000884": "66014",
            "WMC:E14000885": "65673",
            "WMC:E14000882": "65917",
            "WMC:E14000883": "65566",
            "WMC:E14000880": "65737",
            "WMC:E14000881": "65860",
            "WMC:W07000041": "66115",
            "WMC:W07000042": "66112",
            "WMC:W07000043": "66103",
            "WMC:W07000044": "66113",
            "WMC:W07000045": "66117",
            "WMC:E14000888": "65795",
            "WMC:E14000889": "65973",
            "WMC:E14000550": "65687",
            "WMC:E14000551": "65725",
            "WMC:E14000552": "65561",
            "WMC:E14000805": "65645",
            "WMC:E14000901": "65884",
            "WMC:E14000802": "65896",
            "WMC:E14000900": "66077",
            "WMC:E14000555": "65853",
            "WMC:E14000800": "65887",
            "WMC:E14000557": "65845",
            "WMC:E14000688": "65991",
            "WMC:E14000689": "65677",
            "WMC:E14000839": "65702",
            "WMC:E14000838": "65658",
            "WMC:S14000051": "14448",
            "WMC:E14000833": "65664",
            "WMC:E14000832": "65594",
            "WMC:E14000831": "66055",
            "WMC:E14000908": "65736",
            "WMC:E14000837": "65602",
            "WMC:E14000836": "65918",
            "WMC:E14000835": "65828",
            "WMC:E14000834": "65861",
            "WMC:E14000583": "66071",
            "WMC:E14000582": "65969",
            "WMC:E14000853": "65720",
            "WMC:E14000852": "65605",
            "WMC:E14000855": "65565",
            "WMC:W07000048": "66091",
            "WMC:E14000682": "65780",
            "WMC:E14000854": "66024",
            "WMC:E14000683": "65979",
            "WMC:E14000857": "65894",
            "WMC:E14000584": "65993",
            "WMC:E14000538": "65739",
            "WMC:E14000539": "66008",
            "WMC:E14000536": "65811",
            "WMC:E14000537": "66056",
            "WMC:E14000534": "65784",
            "WMC:E14000535": "65895",
            "WMC:E14000532": "65892",
            "WMC:E14000533": "65809",
            "WMC:E14000530": "65730",
            "WMC:E14000531": "65773",
            "WMC:E14000907": "65589",
            "WMC:E14000906": "65681",
            "WMC:E14000905": "65656",
            "WMC:E14000904": "66029",
            "WMC:E14000903": "65930",
            "WMC:E14000902": "66019",
            "WMC:S14000059": "14456",
            "WMC:S14000058": "14455",
            "WMC:S14000057": "14454",
            "WMC:S14000056": "14453",
            "WMC:S14000055": "14452",
            "WMC:S14000054": "14451",
            "WMC:S14000053": "14450",
            "WMC:S14000052": "14449",
            "WMC:E14000909": "65833",
            "WMC:S14000050": "14447",
            "WMC:E14000718": "65837",
            "WMC:E14000719": "65838",
            "WMC:E14000712": "65996",
            "WMC:E14000713": "65928",
            "WMC:E14000710": "65551",
            "WMC:E14000711": "65864",
            "WMC:E14000716": "65600",
            "WMC:E14000717": "65627",
            "WMC:E14000714": "65683",
            "WMC:E14000715": "65944",
            "WMC:E14000653": "65572",
            "WMC:N06000004": "66127",
            "WMC:E14000651": "65877",
            "WMC:E14000650": "65575",
            "WMC:E14000657": "65985",
            "WMC:E14000656": "65923",
            "WMC:E14000655": "65867",
            "WMC:N06000005": "66128",
            "WMC:E14000659": "66011",
            "WMC:E14000658": "65802",
            "WMC:W07000060": "66116",
            "WMC:E14001029": "65983",
            "WMC:E14001028": "65588",
            "WMC:E14001023": "65961",
            "WMC:E14001022": "66004",
            "WMC:E14001021": "65626",
            "WMC:E14001020": "66049",
            "WMC:E14001027": "65740",
            "WMC:E14001026": "65560",
            "WMC:E14001025": "65830",
            "WMC:W07000067": "66089",
            "WMC:W07000064": "66110",
            "WMC:W07000065": "66102",
            "WMC:E14000998": "65554",
            "WMC:E14000999": "65692",
            "WMC:E14000990": "65976",
            "WMC:E14000991": "65789",
            "WMC:E14000992": "65977",
            "WMC:E14000993": "65686",
            "WMC:E14000994": "65905",
            "WMC:E14000995": "65919",
            "WMC:E14000996": "65761",
            "WMC:E14000997": "65744",
            "WMC:E14000879": "65974",
            "WMC:E14000878": "65649",
            "WMC:E14000877": "66081",
            "WMC:E14000876": "66002",
            "WMC:E14000875": "65668",
            "WMC:E14000874": "65564",
            "WMC:E14000873": "66060",
            "WMC:E14000872": "65682",
            "WMC:E14000871": "66022",
            "WMC:E14000870": "65903",
            "WMC:W07000071": "66086",
            "WMC:W07000070": "66105",
            "WMC:W07000073": "66095",
            "WMC:N06000018": "66141",
            "WMC:W07000075": "66087",
            "WMC:W07000074": "66107",
            "WMC:W07000046": "66083",
            "WMC:W07000076": "66106",
            "WMC:N06000013": "66136",
            "WMC:N06000012": "66135",
            "WMC:N06000011": "66134",
            "WMC:N06000010": "66133",
            "WMC:N06000017": "66140",
            "WMC:N06000016": "66139",
            "WMC:N06000015": "66138",
            "WMC:N06000014": "66137",
            "WMC:W07000047": "66118",
            "WMC:E14001024": "65769",
            "WMC:W07000080": "66119",
            "WMC:E14000572": "65750",
            "WMC:E14000573": "65679",
            "WMC:E14000570": "65981",
            "WMC:E14000571": "65583",
            "WMC:E14000576": "65841",
            "WMC:E14000577": "65628",
            "WMC:E14000574": "65805",
            "WMC:E14000575": "65753",
            "WMC:E14000578": "65646",
            "WMC:E14000579": "65712",
            "WMC:W07000079": "66114",
            "WMC:E14000617": "65927",
            "WMC:E14000616": "65826",
            "WMC:E14000615": "65913",
            "WMC:E14000614": "65906",
            "WMC:E14000613": "66035",
            "WMC:E14000612": "65975",
            "WMC:E14000611": "66015",
            "WMC:E14000610": "65708",
            "WMC:E14000619": "65878",
            "WMC:E14000618": "65790",
            "WMC:W07000078": "66098",
            "WMC:E14001062": "66037",
            "WMC:E14001061": "65965",
            "WMC:E14001060": "65935",
            "WMC:E14000958": "65728",
            "WMC:E14000959": "65942",
            "WMC:E14000954": "65956",
            "WMC:E14000955": "66016",
            "WMC:E14000956": "65580",
            "WMC:E14000957": "65876",
            "WMC:E14000950": "65775",
            "WMC:E14000951": "65596",
            "WMC:E14000952": "65652",
            "WMC:E14000953": "65678",
            "WMC:S14000004": "14401",
            "WMC:S14000005": "14402",
            "WMC:S14000006": "14403",
            "WMC:S14000007": "14404",
            "WMC:S14000001": "14398",
            "WMC:S14000002": "14399",
            "WMC:S14000003": "14400",
            "WMC:S14000008": "14405",
            "WMC:S14000009": "14406",
            "WMC:E14000763": "65937",
            "WMC:E14000762": "65791",
            "WMC:E14000761": "65925",
            "WMC:E14000760": "65585",
            "WMC:E14000767": "65968",
            "WMC:E14000766": "65871",
            "WMC:E14000765": "66026",
            "WMC:E14000764": "65882",
            "WMC:E14000680": "65569",
            "WMC:E14000681": "65856",
            "WMC:E14000769": "66001",
            "WMC:E14000768": "65939",
            "WMC:E14000684": "65714",
            "WMC:E14000685": "65881",
            "WMC:E14000686": "65756",
            "WMC:E14000687": "65570",
            "WMC:S14000019": "14416",
            "WMC:S14000018": "14415",
        }
        # HACK
        slug = area_2015_map.get(mp_post.slug)
        current_candidacies_2015 = set()
        past_candidacies_2015 = set()
        if slug:
            other_post = Post.objects.get(slug=slug)
            current_candidacies_2015, past_candidacies_2015 = split_candidacies(
                election,
                other_post.memberships.select_related("person", "party").filter(
                    post_election__election__slug="2015"
                ),
            )

        # HACK

        past_candidacies = past_candidacies.union(past_candidacies_2015)

        current_candidates = {c.person for c in current_candidacies}
        past_candidates = {c.person for c in past_candidacies}

        current_candidates = current_candidates.union(
            {c.person for c in current_candidacies_2015}
        )
        past_candidates = past_candidates.union(
            {c.person for c in past_candidacies_2015}
        )

        other_candidates = past_candidates - current_candidates

        elected, unelected = split_by_elected(election, current_candidacies)

        # Now split those candidates into those that we know aren't
        # standing again, and those that we just don't know about.
        not_standing_candidates = {
            p for p in other_candidates if election in p.not_standing.all()
        }
        might_stand_candidates = {
            p for p in other_candidates if election not in p.not_standing.all()
        }
        might_stand_candidates = {
            p for p in might_stand_candidates if p.death_date == ""
        }

        not_standing_candidacies = [
            c for c in past_candidacies if c.person in not_standing_candidates
        ]
        might_stand_candidacies = [
            c for c in past_candidacies if c.person in might_stand_candidates
        ]

        context["candidacies_not_standing_again"] = group_candidates_by_party(
            election, not_standing_candidacies
        )

        context["candidacies_might_stand_again"] = group_candidates_by_party(
            election, might_stand_candidacies
        )

        context["elected"] = group_candidates_by_party(
            election, elected, show_all=True
        )

        context["unelected"] = group_candidates_by_party(election, unelected)

        context["has_elected"] = (
            len(context["elected"]["parties_and_people"]) > 0
        )

        context["show_retract_result"] = False
        number_of_winners = 0
        for c in current_candidacies:
            if c.elected:
                number_of_winners += 1
            if c.elected is not None:
                context["show_retract_result"] = True

        max_winners = get_max_winners(pee)
        context["show_confirm_result"] = bool(max_winners)

        context["add_candidate_form"] = NewPersonForm(
            election=election.slug,
            initial={
                ("constituency_" + election.slug): post_id,
                ("standing_" + election.slug): "standing",
            },
            hidden_post_widget=True,
        )

        context = get_person_form_fields(context, context["add_candidate_form"])
        context["identifiers_formset"] = PersonIdentifierFormsetFactory()

        return context


class LockBallotView(GroupRequiredMixin, UpdateView):
    required_group_name = TRUSTED_TO_LOCK_GROUP_NAME

    http_method_names = ["post"]
    model = PostExtraElection
    slug_url_kwarg = "ballot_id"
    slug_field = "ballot_paper_id"
    form_class = ToggleLockForm

    def form_valid(self, form):
        with transaction.atomic():
            pee = form.instance

            self.object = form.save()
            if hasattr(pee, "rawpeople"):
                # Delete the raw import, as it's no longer useful
                self.object.rawpeople.delete()

            lock = self.object.candidates_locked
            post_name = pee.post.short_label
            if lock:
                suffix = "-lock"
                pp = "Locked"
                # If we're locking this, then the suggested posts
                # can be deleted
                pee.suggestedpostlock_set.all().delete()
            else:
                suffix = "-unlock"
                pp = "Unlocked"
            message = pp + " ballot {} ({})".format(
                post_name, pee.ballot_paper_id
            )

            LoggedAction.objects.create(
                user=self.request.user,
                action_type="constituency-{}".format(suffix),
                ip_address=get_client_ip(self.request),
                post_election=pee,
                source=message,
            )
        if self.request.is_ajax():
            return JsonResponse({"locked": pee.candidates_locked})
        else:
            return HttpResponseRedirect(pee.get_absolute_url())


class BallotPaperCSVView(DetailView):
    queryset = PostExtraElection.objects.select_related("election", "post")
    slug_url_kwarg = "ballot_id"
    slug_field = "ballot_paper_id"

    def get(self, request, *args, **kwargs):
        pee = self.get_object()
        memberships_dict, elected = memberships_dicts_for_csv(
            election_slug=pee.election.slug, post_slug=pee.post.slug
        )

        filename = "{ballot_paper_id}.csv".format(
            ballot_paper_id=pee.ballot_paper_id
        )
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="%s"' % filename
        response.write(list_to_csv(memberships_dict[pee.election.slug]))
        return response


class SOPNForBallotView(DetailView):
    """
    A view to show a single SOPN for a ballot paper
    """

    model = PostExtraElection
    slug_url_kwarg = "ballot_id"
    slug_field = "ballot_paper_id"
    template_name = "elections/sopn_for_ballot.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["documents_with_same_source"] = OfficialDocument.objects.filter(
            source_url=self.object.sopn.source_url
        )

        return context
