import csv
import requests
from django.core.management.base import BaseCommand
from ynr import settings


class Command(BaseCommand):
    """this command creates a csv file with the data from the xml file"""

    def handle(self, **options):
        url = settings.MODGOV_URL
        response = requests.get(url, stream=True)
        from lxml import etree

        root = etree.fromstring(response.content)
        for row in root.findall("Site"):
            id = row.attrib["id"]
            title = row.attrib["title"]
            url = row.attrib["url"]
            row = {
                "id": id,
                "title": title,
                "url": url,
            }

            # create a csv file that has keys as the header row and values as the data
            with open("mg_urls.csv", "a") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=row.keys())
                writer.writerow(row)
