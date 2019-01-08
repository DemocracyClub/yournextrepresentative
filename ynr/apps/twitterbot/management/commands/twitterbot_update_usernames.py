from django.db import transaction
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _

from people.models import Person

from ..twitter import TwitterAPIData
from twitterbot.helpers import TwitterBot


VERBOSE = False


def verbose(*args, **kwargs):
    if VERBOSE:
        print(*args, **kwargs)


class Command(BaseCommand):

    help = (
        "Use the Twitter API to check / fix Twitter screen names and user IDs"
    )

    def handle_person(self, person):
        twitter_identifiers = person.get_identifiers_of_type("twitter_username")

        # If they have any Twitter user IDs, then check to see if we
        # need to update the screen name from that; if so, update
        # the screen name.  Skip to the next person. This catches
        # people who have changed their Twitter screen name, or
        # anyone who had a user ID set but not a screen name
        # (which should be rare).  If the user ID is not a valid
        # Twitter user ID, it is deleted.
        for identifier in twitter_identifiers:
            screen_name = identifier.value or None
            user_id = identifier.internal_identifier

            if user_id:
                verbose(
                    _("{person} has a Twitter user ID: {user_id}").format(
                        person=person, user_id=user_id
                    )
                )
                if user_id not in self.twitter_data.user_id_to_screen_name:
                    print(
                        _(
                            "Removing user ID {user_id} for {person_name} as it is not a valid Twitter user ID. {person_url}"
                        ).format(
                            user_id=user_id,
                            person_name=person.name,
                            person_url=person.get_absolute_url(),
                        )
                    )
                    self.twitterbot.save(
                        person,
                        msg="This Twitter user ID no longer exists; removing it ",
                    )
                    if screen_name:
                        self.twitterbot.save(
                            person,
                            msg="This Twitter screen name no longer exists; removing it ",
                        )
                    identifier.delete()

                    return
                correct_screen_name = self.twitter_data.user_id_to_screen_name[
                    user_id
                ]
                if not screen_name or screen_name != correct_screen_name:
                    msg = "Correcting the screen name from {old_screen_name} to {correct_screen_name}".format(
                        old_screen_name=screen_name,
                        correct_screen_name=correct_screen_name,
                    )
                    print(msg)
                    identifier.value = correct_screen_name
                    identifier.save()
                    self.twitterbot.save(person, msg)
                else:
                    verbose(
                        _(
                            "The screen name ({screen_name}) was already correct"
                        ).format(screen_name=screen_name)
                    )

            # Otherwise, if they have a Twitter screen name (but no
            # user ID, since we already dealt with that case) then
            # find their Twitter user ID and set that as an identifier.
            # If the screen name is not a valid Twitter screen name, it
            # is deleted.
            elif screen_name:
                verbose(
                    _(
                        "{person} has Twitter screen name ({screen_name}) but no user ID"
                    ).format(person=person, screen_name=screen_name)
                )
                if (
                    screen_name.lower()
                    not in self.twitter_data.screen_name_to_user_id
                ):
                    print(
                        _(
                            "Removing screen name {screen_name} for {person_name} as it is not a valid Twitter screen name. {person_url}"
                        ).format(
                            screen_name=screen_name,
                            person_name=person.name,
                            person_url=person.get_absolute_url(),
                        )
                    )
                    identifier.value = ""
                    identifier.save()
                    return
                print(
                    _("Adding the user ID {user_id}").format(
                        user_id=self.twitter_data.screen_name_to_user_id[
                            screen_name.lower()
                        ]
                    )
                )
                person.identifiers.create(
                    scheme="twitter",
                    identifier=self.twitter_data.screen_name_to_user_id[
                        screen_name.lower()
                    ],
                )
                self.twitterbot.save(person)
            else:
                verbose(
                    _("{person} had no Twitter account information").format(
                        person=person
                    )
                )

    def handle(self, *args, **options):
        global VERBOSE
        VERBOSE = int(options["verbosity"]) > 1
        self.twitterbot = TwitterBot()
        self.twitter_data = TwitterAPIData()
        self.twitter_data.update_from_api()
        # Now go through every person in the database and check their
        # Twitter details. This can take a long time, so use one
        # transaction per person.
        for person_id in Person.objects.order_by("name").values_list(
            "pk", flat=True
        ):
            with transaction.atomic():
                # n.b. even though it's inefficient query-wise, we get
                # each person from the database based on their ID
                # within the transaction because the loop we're in
                # takes a long time, other otherwise we might end up
                # with out of date information (e.g. this has happened
                # with the person.versions field, with confusing
                # results...)
                person = Person.objects.get(pk=person_id)
                self.handle_person(person)
