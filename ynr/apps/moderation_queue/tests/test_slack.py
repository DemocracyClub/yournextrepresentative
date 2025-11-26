import json

from candidates.models.db import LoggedAction
from candidates.tests.auth import TestUserMixin
from django.test import TestCase
from moderation_queue.slack import FlaggedEditSlackPoster
from people.tests.factories import PersonFactory

# The key thing about this bio is that it is more than 3,000 characters of text
REALLY_LONG_BIOGRAPHY = """
I know a lot of people are torn on this local election for the Hetton Ward seat onto Sunderland City Council.
All I can say is vote with your heart and do what's best for you.
All I ask is remember that your Independent councillors have been working for you for the past 11 years. Very hard years, We've had to battle the Labour party who ran Hetton Town Council for 40 years. They all walked away. In many instances we've had to fight to retain Hetton Town Council with Sunderland City Council.
We've never given up on retaining Hetton Town Council Why ? Because it gives the residents a voice.
But more importantly we have represented many many families with very difficult situations and giving advice and much needed support on a personal level.
Here are just a few examples and successfully fought cases.
1.Represented residents with housing problems such as social housing damp and green mould in a child's bedroom who had asthma, This was resolved successfully.
2. Fighting the application for Manor House to be used as a HMO it was me as an Independent councillor who called for public meetings at ELCAP the first meeting with over 100 residents attending.
3. Second meeting was at the Hetton Centre again very well attended and vocal. I will add I invited all the Labour party City councillors and our MP none attended, However I did ask the owner of Manor House at the meeting to withdraw his application and he agreed. That's the role of a councillor, You work for the residents and build a strong relationship with the community.
That outcome shows what we can achieve together, If no one fought that application who knows what the outcome would have led to.
4. The shop on station road is another fight we actually made a difference with the fight, That was earmarked for approval by Sunderland City Council I alongside residents spoke against the application and the planning committee listened and agreed to withdraw the approval,As always the applicant can go to the planning inspectorate and appeal they did and it was overturned, However it shows how fighting together works and the Independent councillors have constantly demonstrated their commitment to the area and to the residents who ask and need help.
5. Antisocial behaviour. This one was controversial. I made comments about Hetton Town Centre turning into the Wild West as you can imagine it caused a whirlwind of interest, That was the whole point of saying it to get peoples attention, It certainly did that, The Echo , The Chronicle and BBC radio Newcastle All contacted me for the facts , issues and problems. I spoke to BBC radio Newcastle live at 6 O'clock in the early hours of the morning and gave a no holes barred interview..
The outcome was Northumbria Police acting and conducting operation Avalanche which resulted in 28 arrests for various offences.
6. Memorial Park in the centre of Hetton, Unsafe condition for veterans when laying down wreath for remembrance day. Repeated requests for the appropriate people to actually make it safe costs depending on what was best suited ranged from £4.500 pounds for the basic gravel surface to £23,000 pounds for a strong sound permanent long lasting surface. I took the opportunity to address a large building provider and they said they could help they d is did it within weeks at no cost at all to Hetton Town Council, So being proactive and not shy to ask or indeed challenge in different circumstances is something I'm definitely not afraid to do.

So when you vote it's not what people promise it's what people have done over a period of time to help improve the area and give support when it matters.
I could give you all hundreds of examples of how your Independent councillors have helped and made a difference
"""


class TestFlaggedEditSlackPoster(TestUserMixin, TestCase):
    def test_format_message(self):
        action = LoggedAction.objects.create(
            user=self.user,
            action_type="person-update",
            popit_person_new_version="8aa71db8f2f20bf8",
            source="test",
        )

        person = PersonFactory.create(
            id="9876",
            name="Test Candidate",
            versions=[
                {
                    "user": "john",
                    "information_source": "Manual correction by a user",
                    "timestamp": "2015-06-10T05:35:15.297559",
                    "version_id": "8aa71db8f2f20bf8",
                    "data": {
                        "id": "9876",
                        "Candidate Name": "Test Candidate",
                    },
                },
                {
                    "information_source": "Updated by a script",
                    "timestamp": "2015-05-08T01:52:27.061038",
                    "version_id": "643dc3343880f168",
                    "data": {
                        "id": "9876",
                    },
                },
            ],
        )

        action.person = person

        poster = FlaggedEditSlackPoster(action)
        msg = poster.format_message()
        parsed = json.loads(msg)

        self.assertGreaterEqual(len(parsed), 3)
        header = parsed[1]
        self.assertEqual(header["type"], "section")

        header_text = header["text"]["text"]
        self.assertIn("One of the first 3 edits of user john", header_text)
        self.assertIn("/person/9876", header_text)

        # Last block should be actions with an Approve button
        actions = parsed[-1]
        self.assertEqual(actions["type"], "actions")
        elements = actions["elements"]
        approve = elements[0]
        self.assertEqual(approve["text"]["text"], "Approve")
        self.assertEqual(approve["value"], str(action.pk))

    def test_format_message_with_long_candidate_statement(self):
        action = LoggedAction.objects.create(
            user=self.user,
            action_type="person-update",
            popit_person_new_version="8aa71db8f2f20bf8",
            source="test",
        )

        person = PersonFactory.create(
            id="9876",
            name="Test Candidate",
            versions=[
                {
                    "user": "john",
                    "information_source": "Manual correction by a user",
                    "timestamp": "2015-06-10T05:35:15.297559",
                    "version_id": "8aa71db8f2f20bf8",
                    "data": {
                        "id": "9876",
                        "biography": REALLY_LONG_BIOGRAPHY,
                    },
                },
                {
                    "information_source": "Updated by a script",
                    "timestamp": "2015-05-08T01:52:27.061038",
                    "version_id": "643dc3343880f168",
                    "data": {
                        "id": "9876",
                        "Candidate Name": "Test Candidate",
                    },
                },
            ],
        )

        action.person = person

        poster = FlaggedEditSlackPoster(action)
        msg = poster.format_message()
        parsed = json.loads(msg)

        self.assertTrue(len(parsed[4]["text"]["text"]) < 3000)
