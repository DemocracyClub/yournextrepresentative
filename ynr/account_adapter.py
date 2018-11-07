import logging

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

logger = logging.getLogger(__name__)


class NoNewUsersAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        """
        Checks whether or not the site is open for signups.

        Next to simply returning True/False you can also intervene the
        regular flow by raising an ImmediateHttpResponse

        (Comment reproduced from the overridden method.)
        """
        return False


class LoggingSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Exactly the same as the DefaultSocialAccountAdapter, but logs authentication
    errors to the default log.

    """

    def authentication_error(
        self,
        request,
        provider_id,
        error=None,
        exception=None,
        extra_context=None,
    ):
        """
        Log errors to authenticating. This method in the parent class is
        left blank and exists for overriding, so we can do what we want here.

        """
        logger.error(
            "Error logging in with provider '{}' with error '{}' ({})".format(
                provider_id, error, exception
            )
        )
