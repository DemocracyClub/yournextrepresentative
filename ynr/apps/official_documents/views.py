from auth_helpers.views import GroupRequiredMixin
from candidates.models import Ballot, LoggedAction
from candidates.models.db import ActionType
from candidates.views.version_data import get_client_ip
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views.generic import CreateView, DetailView, TemplateView
from moderation_queue.models import SuggestedPostLock
from sopn_parsing.helpers.extract_pages import (
    extract_pages_for_ballot,
)
from sopn_parsing.helpers.extract_tables import extract_ballot_table
from sopn_parsing.helpers.parse_tables import parse_raw_data_for_ballot
from sopn_parsing.helpers.text_helpers import NoTextInDocumentError

from .forms import UploadDocumentForm
from .models import DOCUMENT_UPLOADERS_GROUP_NAME, OfficialDocument


class CreateDocumentView(GroupRequiredMixin, CreateView):
    required_group_name = DOCUMENT_UPLOADERS_GROUP_NAME

    form_class = UploadDocumentForm
    template_name = "official_documents/upload_document_form.html"

    def get_initial(self):
        return {
            "ballot": Ballot.objects.get(
                ballot_paper_id=self.kwargs["ballot_paper_id"]
            ),
            "document_type": OfficialDocument.NOMINATION_PAPER,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ballot = get_object_or_404(
            Ballot, ballot_paper_id=self.kwargs["ballot_paper_id"]
        )
        context["post_label"] = ballot.post.label
        return context

    def form_valid(self, form):
        """
        Saves the SOPN and attempts to parse the PDF to extract the candidate
        information. This fails silently to avoid a 500 error if the PDF cannot
        be parsed. We always save the file even if it cannot be parsed, then
        create a LoggedAction and redirect the user.
        """
        self.object = form.save()
        try:
            if hasattr(self.object.ballot, "rawpeople"):
                self.object.ballot.rawpeople.delete()
            extract_pages_for_ballot(ballot=self.object.ballot)
            extract_ballot_table(ballot=self.object.ballot)
            parse_raw_data_for_ballot(ballot=self.object.ballot)
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

        return HttpResponseRedirect(self.get_success_url())


class PostsForDocumentView(DetailView):
    model = OfficialDocument
    template_name = "official_documents/posts_for_document.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        documents = (
            OfficialDocument.objects.filter(source_url=self.object.source_url)
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

        SOPNs_qs = OfficialDocument.objects.filter(
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
