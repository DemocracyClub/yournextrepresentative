from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dateutil import parser
from elections.models import Election
from resultsbot.matchers.candidate import CandidateMatcher
from resultsbot.matchers.mappings import SavedMapping
from resultsbot.matchers.party import PartyMatacher
from uk_results.utils import calculate_turnout_percentage

from .base import BaseCandidate, BaseDivision, BaseImporter

requests.packages.urllib3.disable_warnings()


class ModGovCandidate(BaseCandidate):
    def __init__(self, candidate_xml, division):
        self.division = division
        self.xml = candidate_xml
        if isinstance(candidate_xml, str):
            self.soup = BeautifulSoup(self.xml, "xml")
        else:
            self.soup = candidate_xml

    @property
    def name(self):
        return self.soup.candidatename.get_text(strip=True)

    @property
    def party_name(self):
        return self.soup.politicalpartytitle.get_text(strip=True)

    @property
    def party(self):
        return PartyMatacher(self.party_name, division=self.division).match()

    @property
    def ynr_membership(self):
        return CandidateMatcher(self, self.division).match()

    @property
    def votes(self):
        return int(self.soup.numvotes.get_text(strip=True))


class ModGovDivision(BaseDivision):
    def __init__(self, election, soup, matched=None):
        """
        Take the whole `electionarea` XML
        """
        self.soup = soup
        title = soup.title.get_text(strip=True)
        if not matched:
            matched = set()
        self.matched = matched
        super().__init__(election, title)
        ATTRS = [
            "electionareaid",
            "title",
            "description",
            "externallink",
            "population",
            "electorate",
            "numballotpapersissued",
            "numproxyvotes",
            "numpostalvotessent",
            "numpostalvotesreturned",
            "startvotedatetime",
            "endvotedatetime",
            "endofcountingdatetime",
            "numseats",
            "status",
        ]
        for attr in ATTRS:
            soup_attr = getattr(soup, attr)
            if soup_attr:
                value = soup_attr.get_text(strip=True)
                if attr.startswith("num") or attr == "electorate":
                    value = int(value)
                setattr(self, attr, value)

    @property
    def spoiled_votes(self):
        if not self.soup.spoiledvotes:
            return None

        spoiled_vote_count = 0

        for spoiled_vote in self.soup.spoiledvotes.find_all("spoiledvote"):
            try:
                if spoiled_vote.numvotes:
                    spoiled_vote_count += int(
                        spoiled_vote.numvotes.get_text(strip=True)
                    )
            except ValueError:
                pass

        if not spoiled_vote_count:
            return None
        return spoiled_vote_count

    @property
    def turnout_percentage(self):
        if not all([self.numballotpapersissued, self.electorate]):
            return None
        return calculate_turnout_percentage(
            self.numballotpapersissued, self.electorate
        )


class ModGovImporter(BaseImporter):
    def __init__(self, *args, **kwargs):
        self.url = kwargs.pop("url")
        super().__init__(*args, **kwargs)
        self.get_data()
        self.saved_numseats = SavedMapping("num_seats.json")

    def get_data(self):
        try:
            self.data = requests.get(
                self.url,
                headers={
                    "Connection": "keep-alive",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0",
                    "Upgrade-Insecure-Requests": "1",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate",
                },
                verify=False,
            ).content
            self.soup = BeautifulSoup(self.data, "xml")
        except requests.RequestException:
            print("Error getting {}".format(self.url))

    def divisions(self):
        if not self.soup or not self.soup.election:
            return []
        areas = self.soup.election.find_all("electionarea")
        matched = set()
        for area in areas:
            division = ModGovDivision(self.election, area, matched=matched)
            area = division.match_name()
            if area == "--deleted--":
                continue
            if not division.local_area:
                raise ValueError

            matched.add(division.local_area.ballot_paper_id)
            if int(division.numseats) != division.local_area.winner_count:
                if int(division.numseats) == 0:
                    # chances are this is a mistake
                    pass
                else:
                    key = division.local_area.ballot_paper_id
                    should_ask = self.saved_numseats.get(key, True)
                    if should_ask:
                        print(division.title)
                        print(self.url)
                        print(
                            division.numseats, division.local_area.winner_count
                        )
                        print("winner_count mismatch, update local?")
                        answer = input("y/n: ")
                        if answer.lower() == "y":
                            division.local_area.winner_count = int(
                                division.numseats
                            )
                            division.local_area.save()
                        self.saved_numseats[key] = False
                        self.saved_numseats.save()
                    else:
                        pass
            yield division

    def candidates(self, division):
        for candidate in self.soup.find_all("candidate"):
            if candidate.electionareaid.get_text() == division.electionareaid:
                yield ModGovCandidate(candidate, division)

    def api_url_to_web_url(self, url):
        url = url.replace(
            "mgWebService.asmx/GetElectionResults",
            "mgElectionElectionAreaResults.aspx",
        )
        return url.replace("lElectionId=", "Page=all&EID=")


class ModGovElection(object):
    """
    A wrapper around the election XML from modgov
    """

    def __init__(self, xml):
        self.raw_xml = xml
        self.soup = BeautifulSoup(xml, "xml")

    @property
    def title(self):
        try:
            return self.soup.election.title.get_text(strip=True)
        except:
            raise

    @property
    def num_candidates(self):
        return len(self.soup.find_all("candidate"))

    @property
    def num_divisions(self):
        return len(self.soup.election.find_all("electionarea"))


class ModGovElectionMatcher(object):
    """
    A class that takes a base MovGov install, enumerates all the
    elections it can find and attempts to match them to a YNR election
    """

    def __init__(self, base_domain, election_id):
        base_domain = base_domain.split("//", 1)[-1]
        if not base_domain.endswith("/"):
            base_domain = base_domain + "/"
        self.base_domain = base_domain
        self.start_id = 1
        self.lookahead = 120
        self.elections_by_id = {}
        self.election_obj = Election.objects.get(slug=election_id)
        self.http_only = False

    def format_elections_api_url(self):
        endpoint = "mgWebService.asmx/GetElectionResults"
        url = urljoin(self.base_domain, endpoint)
        return "https://{}?lElectionId=".format(url)

    def format_elections_html_url(self):
        endpoint = "mgElectionElectionAreaResults.aspx"
        url = urljoin(self.base_domain, endpoint)
        url = "https://{}?Page=all&EID=".format(url)
        if self.http_only:
            url = url.replace("https://", "http://")
        return url

    def format_elections_index_url(self):
        endpoint = "mgManageElectionResults.aspx"
        url = urljoin(self.base_domain, endpoint)
        url = "https://{}".format(url)
        if self.http_only:
            url = url.replace("https://", "http://")
        return url

    def parse_remote_date(self, election_id, election):
        """
        The API doesn't return the actual poll date, so we have to scrape
        the HTML!
        """
        req = requests.get(
            "{}{}".format(self.format_elections_html_url(), election_id)
        )
        # print("HTML URL: " + req.url)
        soup = BeautifulSoup(req.text, "html5lib")
        headings = soup.find_all("h2", {"class": "mgSubTitleTxt"})
        for heading in headings:
            if heading.get_text().lower().startswith("parish"):
                continue
            try:
                return parser.parse(
                    heading.get_text().split(" - ")[-1].strip()
                ).date()
            except ValueError:
                print("title_str")
        return None

    def uses_election_feature(self):
        try:
            req = requests.get(self.format_elections_index_url(), timeout=2)
            req.raise_for_status()
        except requests.RequestException:
            self.http_only = True
            req = requests.get(self.format_elections_index_url(), timeout=2)
        print(req.url)
        if "No published elections found." in req.text:
            return False
        return True

    def find_elections(self):
        if not self.uses_election_feature():
            print(
                "Looks like {} doesn't use the election feature".format(
                    self.base_domain
                )
            )
        i = self.start_id
        while i < self.lookahead:
            election = self.get_election_by_id(i)
            if "<election />" not in election.text:
                self.lookahead += 1
                self.elections_by_id[i] = ModGovElection(election.text)
                self.elections_by_id[i].url = election.url
                # print(self.elections_by_id[i].title)
            i = i + 1

    def get_election_by_id(self, election_id):
        base_url = self.format_elections_api_url()
        url = "{}{}".format(base_url, election_id)
        if self.http_only:
            url = url.replace("https://", "http://")

        try:
            req = requests.get(url, timeout=2, verify=False)
            req.raise_for_status()
        except requests.RequestException:
            url = url.replace("https://", "http://")
            req = requests.get(url, timeout=2, verify=False)
            self.http_only = True

        return req

    def match_to_election(self):
        found_elections = {}
        for election_id, election in self.elections_by_id.items():
            election_date = self.parse_remote_date(election_id, election)
            if election_date == self.election_obj.election_date:
                # Great! We have the right date!
                found_elections[election_id] = election
                continue
        if len(found_elections.values()) == 1:
            return list(found_elections.values())[0]
        if len(found_elections.values()) > 1:
            print("Found more than one election for this date!")
            for election_id, election in found_elections.items():
                print("\t{}\t{}".format(election_id, election.title))
            selected = int(input("Pick one: "))
            return found_elections[selected]
        return None
