import requests
from django.conf import settings
from django.core.cache import cache


class TwitterAPITokenMissing(Exception):
    pass


def get_twitter_user_id(twitter_screen_name):
    cache_key = "twitter-screen-name:{}".format(twitter_screen_name)
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result
    token = settings.TWITTER_APP_ONLY_BEARER_TOKEN
    if not token:
        raise TwitterAPITokenMissing()
    headers = {"Authorization": "Bearer {token}".format(token=token)}
    r = requests.get(
        "https://api.twitter.com/2/users/by?usernames=",
        data={"username": twitter_screen_name},
        headers=headers,
    )
    data = r.json()
    if data:
        if "errors" in data:
            all_errors = data["errors"]
            if any(
                d["detail"]
                == f"Could not find user with usernames: [{twitter_screen_name}]"
                for d in all_errors
            ):
                result = ""
            elif any(
                d["detail"]
                == f"User has been suspended: [{twitter_screen_name}]."
                for d in all_errors
            ):
                result = str(data[0]["id"])
            else:
                raise Exception(
                    "The Twitter API says: {error_messages}".format(
                        error_messages=data["errors"]
                    )
                )
        else:
            result = str(data[0]["id"])
    else:
        result = ""
    # Cache Twitter screen name -> user ID results for 5 minutes -
    # this is largely so we usually only make one API call for both
    # validating a screen name in a form and acting on submission of
    # that form.
    cache.set(cache_key, result, 60 * 5)
    return result
