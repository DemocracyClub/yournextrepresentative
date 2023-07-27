import json

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from moderation_queue.slack import FlaggedEditSlackReplyer


@method_decorator(csrf_exempt, name="dispatch")
class SlackHookRouter(View):
    """
    A view that receives POST data from Slack and processes it depending
    on the payload.
    """

    def post(self, *args, **kwargs):
        payload = json.loads(self.request.POST["payload"])

        # callback = payload.get('callback_id')
        # print(json.dumps(payload, indent=4))
        # print(callback)
        for action in payload["actions"]:
            if action["action_id"] == "candidate-edit-review-approve":
                FlaggedEditSlackReplyer(payload, action).reply()
        return HttpResponse()
