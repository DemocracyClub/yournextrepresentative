from candidatebot.helpers import CandidateBot
from django.core.management.base import BaseCommand
from people.models import Person
from popolo.models import OtherName

chars_to_replace = {
    "\xa0": " ",
    "\u1680": " ",
    "\u2000": " ",
    "\u2001": " ",
    "\u2002": " ",
    "\u2003": " ",
    "\u2004": " ",
    "\u2005": " ",
    "\u2006": " ",
    "\u2007": " ",
    "\u2008": " ",
    "\u2009": " ",
    "\u200a": " ",
    "\u202f": " ",
    "\u205f": " ",
    "\u3000": " ",
}


def replace_char(name, char, replace):
    name = name.replace(char, replace)
    return " ".join(name.split()).strip()


class Command(BaseCommand):
    help = "Replaces chars in person names that we don't want to be there."

    def handle(self, *args, **options):
        for char, replace in chars_to_replace.items():
            qs = Person.objects.filter(name__contains=char).only("pk", "name")
            for person in qs:
                for other_name in person.other_names.all():
                    other_name.name = replace_char(
                        other_name.name, char, replace
                    )
                    other_name.save()
                bot = CandidateBot(person_id=person.pk, update=True)
                bot.edit_field("name", replace_char(person.name, char, replace))
                bot.save(
                    f"Replacing {repr(char)} with {repr(replace)} in person name"
                )

            qs = OtherName.objects.filter(name__contains=char)
            for other_name in qs:
                existing_name = other_name.content_object.other_names.filter(
                    name=replace_char(other_name.name, char, replace)
                )
                if existing_name:
                    other_name.delete()
                    continue
                other_name.name = replace_char(other_name.name, char, replace)
                if other_name.name == other_name.content_object.name:
                    other_name.delete()
                else:
                    other_name.save()
                bot = CandidateBot(
                    person_id=other_name.content_object.pk, update=True
                )
                bot.edits_made = True
                bot.save(
                    f"Replacing {repr(char)} with {repr(replace)} in person other name"
                )
