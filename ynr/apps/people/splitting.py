from collections import defaultdict

from candidates.models.versions import (
    is_a_merge,
    version_timestamp_key,
)


class PersonSplitter:
    """This class is responsible for splitting incorrectly merged candidates.
    Inverse of ynr/apps/people/merging.py
    """

    def __init__(self, person):
        self.person = person

    def merged_version(self, person):
        """Search through the person versions for the person merge history.
        and return the last merge version.
        """
        versions_data = self.person.versions
        version_id_to_parent_ids = {}
        if not self.person.versions:
            return version_id_to_parent_ids
        ordered_versions = sorted(versions_data, key=version_timestamp_key)
        person_id_to_ordered_versions = defaultdict(list)
        # Divide all the version with the same ID into separate ordered
        # lists, and record the parent of each version that we get from
        # doing that:
        merged_versions = []
        for version in ordered_versions:
            version_id = version["version_id"]
            person_id = version["data"]["id"]
            versions_for_person_id = person_id_to_ordered_versions[person_id]
            if versions_for_person_id:
                last_version_id = versions_for_person_id[-1]["version_id"]
                version_id_to_parent_ids[version_id] = [last_version_id]
            else:
                version_id_to_parent_ids[version_id] = []
            versions_for_person_id.append(version)
        # Now go through looking for versions that represent merges. Note
        # that it's *possible* for someone to create a new version that
        # doesn't represent a merge but which has a information_source
        # message that makes it look like one. We try to raise an
        # exception if this might have happened, by checking that (a) the
        # person ID in the message also has history in this versions array
        # and (b) the number of unique person IDs in the versions is one
        # more than the number of versions that look like merges. We raise
        # an exception in either of these situations.

        number_of_person_ids = len(person_id_to_ordered_versions.keys())
        number_of_merges = 0
        for version in ordered_versions:
            version_id = version["version_id"]
            merged_from = is_a_merge(version)
            if merged_from:
                number_of_merges += 1
                # TO DO: Do we want the most recent merged version or should we present the user with options?
                merged_versions.append(version)
        if number_of_person_ids != number_of_merges + 1:
            raise ValueError(
                "The number of unique person IDs in the versions is not one more than the number of versions that look like merges."
            )

        return merged_versions[0]["data"]
