# People

This app is for storing people and related information.

Information in this app should be about a person, not about a person's
relationship to an election. For example, their name might change over
time, but the name change isn't a property of an election they are
standing in.

Thing like their political party should be stored on the _candidacy_.
This is currently represented as a `Membership` in the `popolo` app.

# Person Identifiers

`PersonIdentifiers` are used to store contact information and online presence for a candidate. Users can add/edit these identifiers in the person update form. The following fields are available in the `PersonIdentifier` model with the corresponding form labels and accepted formats:
```
email = "Email": Accepts a valid email address; raises an exception if the email is submitted with an invalid format. The email address must be unique.
facebook_page_url = "Facebook Page": Accepts a valid URL but does not currently validate the domain.
facebook_personal_url = "Facebook Personal": Same as above. 
homepage_url = "Homepage": Accepts a valid URL
blog_url = "Blog": Accepts a valid URL
linkedin_url = "Linkedin": Accepts a valid URL; does not currently validate the domain or the format of the username.
party_ppc_page_url = "Party Candidate Page": Accepts a valid URL
twitter_username = "Twitter": Accepts a Twitter username and returns the full Twitter URL.No longer validates the username actually exists.
mastodon_username = "Mastodon": Accepts and returns a valid Mastodon URL and validates the domain and username.
wikipedia_url = "Wikipedia": Accepts a valid URL; does not currently validate the domain.
wikidata_id = "Wikidata": Accepts a valid Wikidata ID
youtube_profile = "YouTube Profile": Accepts a valid URL; does not currently validate the domain.
instagram_url = "Instagram Profile": Accepts and returns a valid Instagram URL and validates the domain and format of the username.
blue_sky_url = "Bluesky URL": Accepts and returns a valid URL
threads_url = "Threads URL": Accepts and returns a valid URL
tiktok_url = "TikTok URL": Accepts and returns a valid URL
other_url = "Other URL": Accepts and returns a valid URL
```