[![Build Status](https://circleci.com/gh/DemocracyClub/yournextrepresentative.svg?style=shield)](https://circleci.com/gh/DemocracyClub/yournextrepresentative)
[![Coverage Status](https://coveralls.io/repos/github/DemocracyClub/yournextrepresentative/badge.svg)](https://coveralls.io/github/DemocracyClub/yournextrepresentative)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
![CodeQL](https://github.com/DemocracyClub/yournextrepresentative/workflows/CodeQL/badge.svg)

# A website for crowd-sourcing structured data about election candidates

[**candidates.democracyclub.org.uk**](https://candidates.democracyclub.org.uk)

YourNextRepresentative ("**YNR**") is an open source platform
for crowd-sourcing information about candidates for political office,
and making it available as open data to anyone.
YNR collects some core data, including:
- who is standing,
- what party they’re standing for,
- their contact details, and
- their social media accounts.

YNR requires that each change is submitted with a source, so that the collected
information can be verified.

## Using YNR

**To find out information** about who you can vote for in upcoming elections, head
over to [whocanivotefor.co.uk](https://whocanivotefor.co.uk) and search for
candidates in your area.

**To contribute information** about candidates, use the YNR application at
[candidates.democracyclub.org.uk](https://candidates.democracyclub.org.uk).

## Developing YNR

Before you can start modifying the YNR application and website, you'll need to
install its development prerequisites -- as detailed in
[`docs/INSTALL.md`](docs/INSTALL.md).

After you've confirmed that the prerequisites are working correctly on your
machine you'll be able to use the workflows detailed in
[`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) to make changes to YNR.

## Known Bugs

You can find a list of known issues to work on here:

* https://github.com/DemocracyClub/yournextrepresentative/issues

## Acknowledgements

This codebase was originally forked from
[mysociety/yournextrepresentative](http://github.com/mysociety/yournextrepresentative)
We no longer track the upstream but we thank [mySociety](https://mysociety.org/)
for their work on the project which we have been able to build on.

## API Versions

v0.9 is legacy code and is now frozen. v1.0 is currently in alpha. We plan on publishing a v1 API once we have some more feedback from users and we think it’s stable enough.

## Statement Of Persons Nominated (SOPN) Parsing

See [`ynr/apps/sopn_parsing`](ynr/apps/sopn_parsing#readme).

## Sentry Error Reporting

Sentry is used to report errors in production. We have added a url for `sentry-debug` to the [`urls.py`](ynr/urls.py#L42) file. This is to allow us verify that Sentry is configured correctly and working in production.

## Pre-election Tasks

### Enable Candidate Leaderboard

The candidate leaderboard shows the most active contributors to the site.
It is a way of encouraging volunteers to add more information about candidates and elections.

We take a slice of edits in YNR and assign them to a election leaderboard. 
This is defined in [`ynr/apps/candidates/views/mixins.py`](ynr/apps/candidates/views/mixins.py#L20).

We can modify the old value to reflect the current election. Change, PR, merge, [currently Sym needs to deploy]

If this is a General Election, the parliamentary candidates can be imported using a google sheet csv url with:
```
podman compose up -d dbpqsl
./scripts/container.run.bash python manage candidatebot_import_next_ppcs --sheet-url SHEET_URL
podman compose down
```
