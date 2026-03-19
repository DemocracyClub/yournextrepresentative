import datetime
import json

from auth_helpers.views import GroupRequiredMixin
from candidates.models import Ballot, LoggedAction
from candidates.models.db import ActionType, EditType
from candidates.views.version_data import get_client_ip
from django.core.files.base import ContentFile
from django.db import transaction
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views.generic import (
    CreateView,
    DetailView,
    TemplateView,
    UpdateView,
)
from elections.models import Election
from moderation_queue.models import SuggestedPostLock
from sopn_parsing.helpers.text_helpers import NoTextInDocumentError

from .extract_pages import ElectionSOPNPageSplitter, clean_matcher_data
from .forms import UploadBallotSOPNForm, UploadElectionSOPNForm
from .models import (
    DOCUMENT_UPLOADERS_GROUP_NAME,
    BallotSOPN,
    ElectionSOPN,
    PageMatchingMethods,
    add_ballot_sopn,
)
from .notifications import send_ballot_sopn_update_notification


class CreateOrUpdateBallotSOPNView(GroupRequiredMixin, UpdateView):
    required_group_name = DOCUMENT_UPLOADERS_GROUP_NAME

    form_class = UploadBallotSOPNForm
    template_name = "official_documents/upload_ballot_sopn_form.html"
    model = BallotSOPN

    def get_initial(self):
        return {
            "ballot": self.ballot,
        }

    def get_object(self, queryset=None):
        self.ballot = Ballot.objects.get(
            ballot_paper_id=self.kwargs["ballot_paper_id"]
        )
        if existing_ballot_sopn := getattr(self.ballot, "sopn", None):
            obj = existing_ballot_sopn
        else:
            obj = self.model()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ballot = get_object_or_404(
            Ballot, ballot_paper_id=self.kwargs["ballot_paper_id"]
        )
        context["ballot"] = ballot
        context["post_label"] = ballot.post.label
        context["general_election"] = self.is_general_election()
        return context

    def form_valid(self, form):
        """
        Saves the SOPN and attempts to parse the PDF to extract the candidate
        information. This fails silently to avoid a 500 error if the PDF cannot
        be parsed. We always save the file even if it cannot be parsed, then
        create a LoggedAction and redirect the user.
        """
        replacement = False
        if self.object.pk:
            replacement = True
        self.object = add_ballot_sopn(
            ballot=form.cleaned_data["ballot"],
            pdf_content=ContentFile(
                form.cleaned_data["uploaded_file"].read(),
                form.cleaned_data["uploaded_file"].name,
            ),
            source_url=form.cleaned_data["source_url"],
            replacement_reason=form.cleaned_data.get("replacement_reason"),
        )
        if replacement:
            send_ballot_sopn_update_notification(self.object, self.request)

        try:
            if hasattr(self.object.ballot, "rawpeople"):
                self.object.ballot.rawpeople.delete()
            # TODO: add back in
            # extract_pages_for_ballot(ballot=self.object.ballot)
            # extract_ballot_table(ballot=self.object.ballot)
            # parse_raw_data_for_ballot(ballot=self.object.ballot)
        except (ValueError, NoTextInDocumentError):
            # If PDF couldn't be parsed continue
            # TODO should be log this error?
            pass

        LoggedAction.objects.create(
            user=self.request.user,
            ballot=self.object.ballot,
            action_type=ActionType.SOPN_UPLOAD,
            ip_address=get_client_ip(self.request),
            source=self.object.source_url,
        )
        self.object.parse()
        return HttpResponseRedirect(self.get_success_url())

    def is_general_election(self):
        return self.ballot.election.slug.startswith(
            "parl"
        ) and self.ballot.election.election_date == datetime.date(2024, 7, 4)


class CreateElectionSOPNView(GroupRequiredMixin, CreateView):
    required_group_name = DOCUMENT_UPLOADERS_GROUP_NAME

    form_class = UploadElectionSOPNForm
    template_name = "official_documents/upload_election_sopn_form.html"

    def get_initial(self):
        return {
            "election": Election.objects.get(slug=self.kwargs["election_id"]),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        election = get_object_or_404(Election, slug=self.kwargs["election_id"])
        context["election"] = election
        return context

    def form_valid(self, form):
        ret = super().form_valid(form)
        LoggedAction.objects.create(
            user=self.request.user,
            election=self.object.election,
            action_type=ActionType.SOPN_UPLOAD,
            ip_address=get_client_ip(self.request),
            source=self.object.source_url,
            edit_type=EditType.USER,
        )
        return ret


class ElectionSOPNMatchingView(GroupRequiredMixin, DetailView):
    required_group_name = DOCUMENT_UPLOADERS_GROUP_NAME
    template_name = "official_documents/election_sopn_matcher.html"
    queryset = (
        ElectionSOPN.objects.all()
        .select_related("election")
        .prefetch_related("election__ballot_set")
    )

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(election__slug=self.kwargs["election_id"])
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        ballots = [
            {
                "ballot_paper_id": ballot.ballot_paper_id,
                "label": ballot.post.label,
                "disabled": hasattr(ballot, "sopn")
                and ballot.sopn.election_sopn_id != self.object.id,
            }
            for ballot in self.object.election.ballot_set.all().order_by(
                "post__label"
            )
        ]

        context["matcher_props"] = {
            "election_id": self.object.election.name,
            "sopn_pdf": self.object.uploaded_file.url,
            "ballots": ballots,
            "pages": self.object.page_mapping,
        }
        return context

    def validate_payload(self, pages):
        # we're making quite a lot of assumptions about this data
        # so we need to be quite strict about checking it on the way in
        if any(value is None for value in pages.values()):
            raise ValueError("All pages must be matched to a value")

        if len(pages.keys()) == 0:
            raise ValueError("Expected 1 or more pages")

        if pages["0"] == ElectionSOPN.CONTINUATION:
            raise ValueError("Fist page can't be a continuation page")

        page_numbers = [int(k) for k, v in pages.items()]
        if not page_numbers == list(
            range(page_numbers[0], page_numbers[0] + len(page_numbers))
        ):
            raise ValueError("Expected a sequential list of pages")

        previous_value = None
        for page_value in pages.values():
            if (
                page_value == ElectionSOPN.CONTINUATION
                and previous_value == ElectionSOPN.NOMATCH
            ):
                raise ValueError(
                    "A continuation page can only follow a ballot page"
                )
            previous_value = page_value

        return True

    @transaction.atomic
    def post(self, request, **kwargs):
        sopn = self.get_object()

        pages = json.loads(request.POST.get("pages"))
        self.validate_payload(pages)

        sopn.blank_pages = [
            k for k, v in pages.items() if v == ElectionSOPN.NOMATCH
        ]
        sopn.save()

        splitter = ElectionSOPNPageSplitter(sopn, clean_matcher_data(pages))
        splitter.split(method=PageMatchingMethods.MANUAL_MATCHED)
        LoggedAction.objects.create(
            user=request.user,
            election=sopn.election,
            action_type=ActionType.SOPN_SPLIT_BALLOTS,
            ip_address=get_client_ip(request),
            source="Manual matching",
            edit_type=EditType.USER,
        )
        return HttpResponseRedirect(sopn.get_absolute_url())


class PostsForDocumentView(DetailView):
    model = BallotSOPN
    template_name = "official_documents/posts_for_document.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        documents = (
            BallotSOPN.objects.filter(source_url=self.object.source_url)
            .distinct("ballot__ballot_paper_id")
            .filter(ballot__election=self.object.ballot.election)
            .select_related("ballot__post", "ballot__election")
            .order_by("ballot__ballot_paper_id")
            .prefetch_related("ballot__suggestedpostlock_set")
        )

        context["document_posts"] = documents

        return context


def get_add_from_document_cta_flash_message(document, remaining_posts):
    return render_to_string(
        "official_documents/_add_from_document_cta_flash_message.html",
        {"document": document, "remaining_posts": remaining_posts},
    )


class UnlockedWithDocumentsView(TemplateView):
    template_name = "official_documents/unlocked_with_documents.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        SOPNs_qs = BallotSOPN.objects.filter(
            ballot__election__current=True
        ).select_related("ballot__election", "ballot__post")

        SOPNs_qs = SOPNs_qs.exclude(
            ballot__post__in=SuggestedPostLock.objects.all().values(
                "ballot__post"
            )
        )

        context["unlocked_sopns"] = SOPNs_qs.filter(
            ballot__candidates_locked=False
        )

        return context
