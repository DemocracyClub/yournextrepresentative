from auth_helpers.views import GroupRequiredMixin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from people.models import Person
from splitting.forms import FIELD_LABELS, OVERRIDE_PREFIX, PersonSplitForm
from splitting.models import TRUSTED_TO_SPLIT_GROUP_NAME
from splitting.splitter import InvalidSplitError, PersonSplitter

# How each kind of suggestion is described in the details table
ACTION_LABELS = {
    "move": "Move",
    "copy": "Copy to both",
    "keep": "Keep",
    "drop": "Leave out",
    "restore": "Put back",
    "review": "Check",
}


def display_value(value):
    if isinstance(value, tuple):
        value = ", ".join(value)
    return value or ""


class PersonSplitView(GroupRequiredMixin, TemplateView):
    """
    Split a candidacy off a person, in two steps: preview the plan (and
    change any choices), then split. Nothing changes until the split is
    confirmed, and only if the choices and the person are the same as when
    the plan was previewed.
    """

    http_method_names = ["get", "post"]
    required_group_name = TRUSTED_TO_SPLIT_GROUP_NAME
    template_name = "splitting/split_person.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.person = get_object_or_404(Person, pk=kwargs["person_id"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["person"] = self.person
        context["edits_allowed"] = self.person.user_can_edit(self.request.user)
        return context

    def get(self, request, *args, **kwargs):
        form = PersonSplitForm(person=self.person)
        return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        form = PersonSplitForm(request.POST, person=self.person)
        context = self.get_context_data(form=form)
        if not context["edits_allowed"] or not form.is_valid():
            return self.render_to_response(context)

        splitter = PersonSplitter(
            self.person,
            form.cleaned_data["membership"].ballot,
            target_person=form.target_person,
            request=request,
            # Moving candidacies and results on locked ballots is what this
            # page is for. It's shown as a warning that has to be ticked.
            allow_locked=True,
            suggest=form.suggest,
            cutoff_days=form.cleaned_data["cutoff_days"],
            move_fields=form.override_fields("move"),
            keep_fields=form.override_fields("keep"),
            move_image=form.cleaned_data["move_image"],
        )
        plan = splitter.plan()
        fingerprint = form.fingerprint()
        context.update(
            {
                "plan": plan,
                "fingerprint": fingerprint,
                "field_rows": self.field_rows(plan, form),
                "other_label": self.other_label(plan),
                "destination_label": plan.destination_label(),
                "result": "Ready to split" if plan.is_valid else "Can't split",
                "confirm_problems": [],
            }
        )

        if request.POST.get("action") != "split":
            return self.render_to_response(context)

        problems = context["confirm_problems"]
        if form.cleaned_data["preview_fingerprint"] != fingerprint:
            problems.append(
                "The choices or the person have changed since the preview. "
                "Check the updated preview below, then split again."
            )
        elif not plan.is_valid:
            problems.append("Fix the errors below before splitting.")
        elif plan.warnings and not form.cleaned_data["warnings_checked"]:
            problems.append(
                "Tick the box to confirm you've checked the warnings."
            )
        if problems:
            return self.render_to_response(context)

        try:
            target = splitter.split()
        except InvalidSplitError as e:
            problems.append(str(e))
            return self.render_to_response(context)

        ballot_id = form.cleaned_data["membership"].ballot.ballot_paper_id
        messages.success(
            request,
            f"Moved {ballot_id} from {self.person.name} ({self.person.pk}) "
            f"to {target.name} ({target.pk}).",
            extra_tags="person-split",
        )
        return HttpResponseRedirect(target.get_absolute_url())

    @staticmethod
    def other_label(plan):
        if plan.target_person:
            return f"{plan.target_person.name} ({plan.target_person.pk})"
        if plan.restore_person_id:
            return (
                f"{plan.new_person_name} ({plan.restore_person_id}, restored)"
            )
        return f"{plan.new_person_name} (new person)"

    @staticmethod
    def field_rows(plan, form):
        rows = []
        for suggestion in plan.field_suggestions:
            if not suggestion.notable:
                continue
            rows.append(
                {
                    "field": suggestion.field,
                    "label": FIELD_LABELS.get(
                        suggestion.field, suggestion.field
                    ),
                    "action": suggestion.action,
                    "action_label": ACTION_LABELS.get(
                        suggestion.action, suggestion.action
                    ),
                    "target_value": display_value(suggestion.target_value),
                    "dest_value": display_value(suggestion.dest_value),
                    "dest_changes": suggestion.dest_value
                    != suggestion.current_value,
                    "reason": suggestion.reason,
                    "override": form[f"{OVERRIDE_PREFIX}{suggestion.field}"],
                }
            )
        return rows
