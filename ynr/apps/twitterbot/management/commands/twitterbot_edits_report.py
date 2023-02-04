from django.core.management.base import BaseCommand

from candidates.diffs import get_version_diffs
from candidates.models import LoggedAction


class Command(BaseCommand):
    def get_correct_version(self, versions, version_id):
        all_version_diffs = get_version_diffs(versions)
        for version_diff in all_version_diffs:
            if version_diff["version_id"] == version_id:
                return version_diff["diffs"]

    def handle(self, *args, **options):
        data_by_person = {}
        qs = LoggedAction.objects.filter(
            user__username="TwitterBot"
        ).select_related("person")
        for la in qs:
            diff = self.get_correct_version(
                la.person.versions, la.popit_person_new_version
            )
            if not diff:
                continue
            for op in diff:
                for parent_diff in op.get("parent_diff", []):
                    if parent_diff["path"] == "twitter_username":
                        if parent_diff["op"] == "replace":
                            if la.person.pk not in data_by_person:
                                data_by_person[la.person.id] = []
                            data_by_person[la.person.id].append(
                                {
                                    "from": parent_diff[
                                        "previous_value"
                                    ].strip(),
                                    "to": parent_diff["value"].strip(),
                                }
                            )

        for person_id, data in data_by_person.items():
            output = [str(person_id)]
            for edit in data:
                if len(output) == 1:
                    output.append(edit["from"])
                output.append(edit["to"])
            print("\t".join(output))
