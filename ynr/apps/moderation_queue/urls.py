from django.urls import re_path

from django.views.decorators.csrf import ensure_csrf_cookie

from .views import (
    PersonNameCleanupView,
    PhotoReview,
    PhotoReviewList,
    PhotoUploadSuccess,
    RemoveSuggestedLocksView,
    SOPNReviewRequiredView,
    SuggestLockReviewListView,
    SuggestLockView,
    upload_photo,
    upload_photo_image,
    upload_photo_url,
)

urlpatterns = [
    re_path(
        r"^photo/upload/(?P<person_id>\d+)$", upload_photo, name="photo-upload"
    ),
    re_path(
        r"^photo/upload/image/(?P<person_id>\d+)$",
        upload_photo_image,
        name="photo-upload-image",
    ),
    re_path(
        r"^photo/upload/url/(?P<person_id>\d+)$",
        upload_photo_url,
        name="photo-upload-url",
    ),
    re_path(
        r"^photo/review$", PhotoReviewList.as_view(), name="photo-review-list"
    ),
    re_path(
        r"^photo/review/(?P<queued_image_id>\d+)$",
        PhotoReview.as_view(),
        name="photo-review",
    ),
    re_path(
        r"^photo/upload/(?P<person_id>\d+)/success$",
        PhotoUploadSuccess.as_view(),
        name="photo-upload-success",
    ),
    re_path(
        r"^suggest-lock/(?P<election_id>.*)/$",
        SuggestLockView.as_view(),
        name="constituency-suggest-lock",
    ),
    re_path(
        r"^suggest-lock/$",
        ensure_csrf_cookie(SuggestLockReviewListView.as_view()),
        name="suggestions-to-lock-review-list",
    ),
    re_path(
        r"^sopn-review-required/$",
        SOPNReviewRequiredView.as_view(),
        name="sopn-review-required",
    ),
    re_path(
        r"^person_name_cleanup/$",
        PersonNameCleanupView.as_view(),
        name="person_name_cleanup",
    ),
    re_path(
        r"^sopn-review-required/remove-ajax/$",
        RemoveSuggestedLocksView.as_view(),
        name="remove-lock-suggestion-ajax",
    ),
]
