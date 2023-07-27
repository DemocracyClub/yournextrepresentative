import requests
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError


class MastodonAPITokenMissing(Exception):
    pass


def verify_mastodon_account(mastodon_domain_name, mastodon_screen_name):
    cache_key = "acct:{}".format(mastodon_screen_name)
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result
    token = settings.MASTODON_APP_ONLY_BEARER_TOKEN
    if not token:
        raise MastodonAPITokenMissing()

    headers = {"Authorization": "Bearer {token}".format(token=token)}
    url = f"https://{mastodon_domain_name}/api/v1/accounts/lookup"
    # if the user exists but the domain doesn't, the API returns a 404 error or times out
    # if the user doesn't exist but the domain does, the API returns a 200 error with an empty list
    # raise an error if the domain doesn't exist
    # if the request timesout, raise an error
    try:
        r = requests.get(
            url,
            params={"acct": mastodon_screen_name},
            headers=headers,
            verify=False,
            timeout=10.0,
        )
    except requests.exceptions.Timeout:
        raise ValidationError(
            "The Mastodon domain '{domain}' doesn't exist. Please check the domain and try again.".format(
                domain=mastodon_domain_name
            )
        )

    data = r.json()

    if data:
        if "error" in data:
            all_errors = data["error"]
            if data["error"] == "Record not found":
                raise ValidationError(
                    "The Mastodon account {screen_name} doesn't exist. Please check the username and try again.".format(
                        screen_name=mastodon_screen_name
                    )
                )
            raise Exception(
                "The Mastodon API returned an error: {error}".format(
                    error=all_errors
                )
            )
        result = str(data["id"])
    else:
        result = ""

    cache.set(cache_key, result, 60 * 5)
    return result
