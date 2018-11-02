from enum import Enum, unique

from .helpers.popolo_fields import simple_fields

SIMPLE_POPOLO_FIELDS = simple_fields


@unique
class PersonIdentifierFields(Enum):
    email = "Email"
    facebook_page_url = "Facebook Page"
    facebook_personal_url = "Facebook Personal"
    homepage_url = "Homepage"
    linkedin_url = "Linkedin"
    party_ppc_page_url = "Party PPC Page"
    twitter_username = "Twitter"
    wikipedia_url = "Wikipedia"
    # party_candidate_page = "Party Candidate Page"
    # other = "Other"
