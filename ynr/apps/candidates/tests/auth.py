from candidates.models import (
    RESULT_RECORDERS_GROUP_NAME,
    TRUSTED_TO_LOCK_GROUP_NAME,
    TRUSTED_TO_MERGE_GROUP_NAME,
)
from django.contrib.auth.models import Group, User
from moderation_queue.models import VERY_TRUSTED_USER_GROUP_NAME
from official_documents.models import DOCUMENT_UPLOADERS_GROUP_NAME
from people.models import TRUSTED_TO_EDIT_NAME


class TestUserMixin(object):
    @classmethod
    def setUpTestData(cls):
        super(TestUserMixin, cls).setUpTestData()
        cls.users_to_delete = []
        for username, attr, group_names in (
            ("TwitterBot", "user", []),
            ("john", "user", []),
            ("alice", "user_who_can_merge", [TRUSTED_TO_MERGE_GROUP_NAME]),
            ("sjorford", "very_trusted_user", [VERY_TRUSTED_USER_GROUP_NAME]),
            ("charles", "user_who_can_lock", [TRUSTED_TO_LOCK_GROUP_NAME]),
            (
                "delilah",
                "user_who_can_upload_documents",
                [DOCUMENT_UPLOADERS_GROUP_NAME],
            ),
            ("ermintrude", "user_who_can_rename", []),
            (
                "frankie",
                "user_who_can_record_results",
                [RESULT_RECORDERS_GROUP_NAME],
            ),
            ("george", "user_can_edit_name", [TRUSTED_TO_EDIT_NAME]),
        ):
            u = User.objects.create_user(
                username, username + "@example.com", "notagoodpassword"
            )
            for group_name in group_names:
                group, _ = Group.objects.get_or_create(name=group_name)
                group.user_set.add(u)
            setattr(cls, attr, u)
            cls.users_to_delete.append(u)
        # Also add a user who hasn't accepted the terms, and isn't in
        # any groups:
        cls.user_refused = User.objects.create_user(
            "johnrefused", "johnrefused@example.com", "notagoodpasswordeither"
        )
        cls.users_to_delete.append(cls.user_refused)
