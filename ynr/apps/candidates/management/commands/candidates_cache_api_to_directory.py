import json
import re
from datetime import datetime
from os.path import join
from urllib.parse import parse_qs, urlsplit

from django.core.files.base import ContentFile
from django.core.files.storage import DefaultStorage
from django.core.management.base import BaseCommand
from django.test import Client


def path_and_query(url):
    split_url = urlsplit(url)
    return split_url.path + "?" + split_url.query


def page_from_url(url):
    page_values = parse_qs(urlsplit(url).query).get("page")
    if page_values:
        return int(page_values[0])
    return 1


def page_filename(endpoint, page_number):
    return "{}-{:06d}.json".format(endpoint, page_number)


def is_timestamped_dir(directory):
    return re.search(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", directory)


class Command(BaseCommand):
    help = "Cache the output of the persons and posts endpoints to a directory"

    endpoints = ("people", "ballots")

    def add_arguments(self, parser):
        parser.add_argument(
            "--hostname",
            action="store",
            default="candidates.democracyclub.org.uk",
            help="Optional hostname if files are stored at a relative path",
        )
        parser.add_argument(
            "--url-prefix",
            help="Optional url_prefix for next and previous links",
        )
        parser.add_argument(
            "--http",
            help="Force URLs to use HTTP. Defaults to HTTPS",
            action="store_true",
        )
        parser.add_argument(
            "--page-size",
            type=int,
            help="How many results should be output per file (max 200)",
        )
        parser.add_argument(
            "--prune",
            action="store_true",
            help=(
                "Prune older timestamped directories (those over 12 hours "
                "old, never deleting the latest successfully generated one "
                "or any of the 4 most recent)"
            ),
        )

    def update_latest_page(self, output_directory, endpoint):
        latest_page_location = join(output_directory, "latest")
        file_name = join(latest_page_location, page_filename(endpoint, 1))
        self.storage.save(file_name, ContentFile(self.first_page_json))

    def prune(self):
        all_dirs = []
        for directory in self.storage.listdir(self.directory_path)[0]:
            if is_timestamped_dir(directory):
                all_dirs.append(directory)

        # Make sure we always leave at least the last 4 directories
        timestamped_directories_to_remove = sorted(all_dirs)[:-4]

        for path in sorted(timestamped_directories_to_remove):
            dir_path = join(self.directory_path, path)
            for filename in self.storage.listdir(dir_path)[1]:
                self.storage.delete(join(dir_path, filename))

    def get_url_prefix(self, url_prefix=None):
        """
        Use the hostname passed if there is one, otherwise try to guess it from
        the DefaultStorage class.

        Raise a ValueError if the hostname isn't an absolute URL

        """

        if not url_prefix:
            url_prefix = self.storage.base_url

        match = "https://" if self.secure else "http://"

        if not url_prefix.startswith(match):
            raise ValueError(
                "URL prefix must start with {}. Try using --url_prefix.".format(
                    match
                )
            )
        return url_prefix

    def rewrite_link(self, endpoint, url):
        if not url:
            return None
        page = page_from_url(url)
        filename = page_filename(endpoint, page)
        return "/".join([self.url_prefix, self.timestamp, filename])

    def get(self, url):
        kwargs = {"SERVER_NAME": self.hostname}
        if self.secure:
            kwargs["wsgi.url_scheme"] = "https"
            kwargs["secure"] = True
        return self.client.get(url, **kwargs)

    def rewrite_next_and_previous_links(self, endpoint, data):
        data["next"] = self.rewrite_link(endpoint, data["next"])
        data["previous"] = self.rewrite_link(endpoint, data["previous"])

    def get_api_results_to_directory(self, endpoint, json_directory, page_size):
        url = "/api/next/{endpoint}/?page_size={page_size}&format=json".format(
            page_size=page_size, endpoint=endpoint
        )

        while url:
            page = page_from_url(url)
            output_filename = join(
                json_directory, page_filename(endpoint, page)
            )
            response = self.get(url)
            if response.status_code != 200:
                msg = "Unexpected response {0} from {1}"
                raise Exception(msg.format(response.status_code, url))
            data = json.loads(response.content.decode("utf-8"))
            original_next_url = data["next"]
            self.rewrite_next_and_previous_links(endpoint, data)

            json_page = json.dumps(data, indent=4, sort_keys=True).encode(
                "utf8"
            )

            if page == 1:
                self.first_page_json = json_page

            self.storage.save(output_filename, ContentFile(json_page))

            # Now make sure the next URL works with the test client:
            if original_next_url:
                url = path_and_query(original_next_url)
            else:
                url = None

    def handle(self, *args, **options):
        self.client = Client()
        self.directory_path = "cached-api"
        self.storage = DefaultStorage()
        self.secure = not options.get("http", False)
        self.hostname = options["hostname"]
        self.url_prefix = self.get_url_prefix(options["url_prefix"])

        self.timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        json_directory = join(self.directory_path, self.timestamp)

        page_size = options["page_size"]
        if not page_size:
            page_size = 200
        for endpoint in self.endpoints:
            self.get_api_results_to_directory(
                endpoint, json_directory, page_size
            )
            self.update_latest_page(self.directory_path, endpoint)
        if options["prune"]:
            self.prune()
