"""

A set of helpers that automate personal data removal. Used in the admin
interface, typically after a GDPR request for removal.

"""
import abc
import json
from collections import defaultdict

DELETED_STR = "<DELETED>"


class BaseCheck(metaclass=abc.ABCMeta):
    def __init__(self, person):
        self.person = person

    def collect(self):
        return {self.__class__.__name__: self.run_collect()}

    @abc.abstractmethod
    def run_collect(self):
        pass

    @abc.abstractmethod
    def run_remove(self):
        pass

    @abc.abstractmethod
    def get_item_display_info(self, item):
        pass


class PhotoCheck(BaseCheck):
    def get_item_display_info(self, item):
        return {
            "title": "image",
            "description": """Source: {source}
            User: {user}
            """.format(
                source=item.source or None, user=item.uploading_user
            ),
            "image": item.image.url,
        }

    def run_collect(self):
        photos_to_remove = []
        for photo in self.person.images.all():
            photos_to_remove.append(self.get_item_display_info(photo))
        return photos_to_remove

    def run_remove(self):
        self.person.images.all().delete()


class VersionHistoryCheck(BaseCheck):
    def get_item_display_info(self, item):
        return {"title": item[0], "description": "\n\t".join(sorted(item[1]))}

    def run_collect(self, do_remove=False):
        version_data_to_remove = []
        never_remove = [
            "death_date",
            "honorific_prefix",
            "id",
            "wikipedia_url",
            "candidacies",
            "name",
            "honorific_suffix",
            "wikidata_id",
            "other_names",
            "slug",
        ]
        never_remove_identifiers = ["uk.org.publicwhip"]
        to_remove = defaultdict(set)
        versions = json.loads(self.person.versions)
        for version in versions:
            for key, value in version.get("data").items():
                if key not in never_remove:
                    if value or value == DELETED_STR:
                        if key == "identifiers":
                            for v in value:
                                if (
                                    not v.get("scheme")
                                    in never_remove_identifiers
                                ):
                                    if v["identifier"] == DELETED_STR:
                                        continue
                                    to_remove[
                                        "Identifier: " + v.get("scheme")
                                    ].add(v["identifier"])
                                    if do_remove:
                                        v["identifier"] = DELETED_STR
                        else:
                            if str(value) == DELETED_STR:
                                continue
                            to_remove[key].add(str(value))
                            if do_remove:
                                version["data"][key] = DELETED_STR

        for remove in to_remove.items():
            if not remove[1]:
                continue
            version_data_to_remove.append(self.get_item_display_info(remove))
        if do_remove:
            self.person.versions = json.dumps(versions)
            self.person.save()
        return version_data_to_remove

    def run_remove(self):
        self.run_collect(do_remove=True)


class DataRemover:
    def __init__(self, person):
        self.person = person
        self.to_remove = {}
        self._collected = False
        self.checks = [PhotoCheck, VersionHistoryCheck]

    def collect(self):
        """
        Runs all checks and collects the data that will be removed without
        performing any actions.
        :return:
        """

        for check in self.checks:
            self.to_remove.update(check(self.person).collect())
        self._collected = True
        return self.to_remove

    def remove(self):
        """
        Removes all data found in the checks.
        :return:
        """
        if not self._collected:
            raise ValueError("Can't remove data without calling collect first")
        for check in self.checks:
            check(self.person).run_remove()
        return self.to_remove
