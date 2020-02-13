from parties.models import Party


class DefaultPartyFixtures:
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        Party.objects.update_or_create(
            ec_id="ynmp-party:12522",
            legacy_slug="ynmp-party:12522",
            defaults={
                "name": "Speaker seeking re-election",
                "date_registered": "1376-04-28",
            },
        )
        Party.objects.update_or_create(
            ec_id="ynmp-party:2",
            defaults={"name": "Independent", "date_registered": "1832-06-07"},
        )
