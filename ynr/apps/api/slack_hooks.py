import json
import logging

import sentry_sdk
from django.http import HttpResponse, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from moderation_queue.slack import FlaggedEditSlackReplyer
from utils.slack import SlackSignatureVerificationError, verify_slack_request

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class SlackHookRouter(View):
    """
    A view that receives POST data from Slack and processes it depending
    on the payload.
    """

    def post(self, *args, **kwargs):
        try:
            verify_slack_request(self.request)
        except SlackSignatureVerificationError as e:
            logger.warning(
                "Rejected POST to slack-hooks: failed signature verification"
            )
            sentry_sdk.capture_exception(e)
            return HttpResponseForbidden()

        payload = json.loads(self.request.POST["payload"])

        # callback = payload.get('callback_id')
        # print(json.dumps(payload, indent=4))
        # print(callback)
        for action in payload["actions"]:
            if action["action_id"] == "candidate-edit-review-approve":
                FlaggedEditSlackReplyer(payload, action).reply()
        return HttpResponse()
