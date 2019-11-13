import re
import unicodedata

from django.core.management.base import BaseCommand
from gender_detector.gender_detector import GenderDetector

from people.models import Person, GenderGuess


class Command(BaseCommand):
    help = "Guess gender based on name or asserted gender"

    def normalize_gender(self, gender):
        """
        Fix common misspellings
        """
        gender = gender.lower()
        map_to_female = (
            "femail",
            "femaile",
            "female",
            "female",
            "femaleale",
            "woman",
        )
        map_to_male = ("m", "mail", "make", "male", "male", "males", "man")
        map_to_non_binary = ("non binary", "non-binary")

        if gender in map_to_female:
            return "female"
        if gender in map_to_male:
            return "male"
        if gender in map_to_non_binary:
            return "non-binary"
        return gender

    def handle(self, *args, **options):
        qs = Person.objects.filter(gender_guess=None)
        detector = GenderDetector("uk")
        for person in qs:
            gender = None
            name = unicodedata.normalize("NFKD", person.name.strip())
            name = re.sub(r"\W+", " ", name)
            if person.gender:
                gender = self.normalize_gender(person.gender)
            else:
                first_name = name.strip().split(" ")[0]
                if first_name:
                    gender = detector.guess(first_name)

            gender_to_code = {
                "male": "M",
                "female": "F",
                "non-binary": "N",
                "unknown": "U",
            }
            if gender_to_code.get(gender, "U") != "U":
                GenderGuess.objects.create(
                    person=person, gender=gender_to_code.get(gender)
                )
