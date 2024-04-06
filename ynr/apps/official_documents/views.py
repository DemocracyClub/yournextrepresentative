import json

from auth_helpers.views import GroupRequiredMixin
from candidates.models import Ballot, LoggedAction
from candidates.models.db import ActionType, EditType
from candidates.views.version_data import get_client_ip
from django.core.files.base import ContentFile
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
    PageMatchingMethods,
    add_ballot_sopn,
    send_ballot_sopn_update_notification,
)


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
        return context

    def form_valid(self, form):
        """
        Saves the SOPN and attempts to parse the PDF to extract the candidate
        information. This fails silently to avoid a 500 error if the PDF cannot
        be parsed. We always save the file even if it cannot be parsed, then
        create a LoggedAction and redirect the user.
        """
        if self.object.pk:
            send_ballot_sopn_update_notification(self.object, self.request)

        self.object = add_ballot_sopn(
            ballot=form.cleaned_data["ballot"],
            pdf_content=ContentFile(
                form.cleaned_data["uploaded_file"].read(),
                form.cleaned_data["uploaded_file"].name,
            ),
            source_url=form.cleaned_data["source_url"],
        )
        try:
            if hasattr(self.object.ballot, "rawpeople"):
                self.object.ballot.rawpeople.delete()
            # TODO: add back in
            # extract_pages_for_ballot(ballot=self.object.ballot)
            # extract_ballot_table(ballot=self.object.ballot)
            # parse_raw_data_for_ballot(ballot=self.object.ballot)
        except (ValueError, NoTextInDocumentError):
            # If PDF couldnt be parsed continue
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
        Election.objects.all()
        .select_related("electionsopn")
        .prefetch_related("ballot_set")
    )
    slug_url_kwarg = "election_id"
    slug_field = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        ballot_data = []
        for ballot in self.object.ballot_set.all().order_by("post__label"):
            ballot_for_matcher = {
                "ballot_paper_id": ballot.ballot_paper_id,
                "label": ballot.post.label,
            }
            if (
                self.object.electionsopn.pages_matched
                and ballot.sopn.relevant_pages != "all"
            ):
                ballot_for_matcher["matched"] = bool(ballot.sopn.relevant_pages)
                ballot_for_matcher["matched_page"] = str(
                    ballot.sopn.first_page_int
                )
            ballot_data.append(ballot_for_matcher)

        context["matcher_props"] = {
            "election_id": self.object.name,
            "sopn_pdf": self.object.electionsopn.uploaded_file.url,
            "ballots": ballot_data,
        }
        return context

    def post(self, request, election_id):
        election = self.get_object()
        splitter = ElectionSOPNPageSplitter(
            election.electionsopn,
            clean_matcher_data(json.loads(request.POST.get("matched_pages"))),
        )
        splitter.split(method=PageMatchingMethods.MANUAL_MATCHED)
        LoggedAction.objects.create(
            user=request.user,
            election=election,
            action_type=ActionType.SOPN_SPLIT_BALLOTS,
            ip_address=get_client_ip(request),
            source="Manual matching",
            edit_type=EditType.USER,
        )
        return HttpResponseRedirect(election.electionsopn.get_absolute_url())


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
