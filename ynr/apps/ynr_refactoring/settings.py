from enum import Enum, unique

from .helpers.popolo_fields import simple_fields

SIMPLE_POPOLO_FIELDS = simple_fields


@unique
class PersonIdentifierFields(Enum):
    email = "Email"
    facebook_page_url = "Facebook Page"
    facebook_personal_url = "Facebook Personal"
    homepage_url = "Homepage"
    blog_url = "Blog"
    linkedin_url = "Linkedin"
    party_ppc_page_url = "Party Candidate Page"
    twitter_username = "Twitter"
    mastodon_username = "Mastodon"
    wikipedia_url = "Wikipedia"
    wikidata_id = "Wikidata"
    youtube_profile = "YouTube Profile"
    instagram_url = "Instagram Profile"
    blue_sky_url = "Bluesky URL"
    threads_url = "Threads URL"
    tiktok_url = "TikTok URL"
    other_url = "Other URL"
    # party_candidate_page = "Party Candidate Page"
    # other = "Other"
