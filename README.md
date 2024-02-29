[![Build Status](https://circleci.com/gh/DemocracyClub/yournextrepresentative.svg?style=shield)](https://circleci.com/gh/DemocracyClub/yournextrepresentative)
[![Coverage Status](https://coveralls.io/repos/github/DemocracyClub/yournextrepresentative/badge.svg)](https://coveralls.io/github/DemocracyClub/yournextrepresentative)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
![CodeQL](https://github.com/DemocracyClub/yournextrepresentative/workflows/CodeQL/badge.svg)


# A website for crowd-sourcing structured election candidate data

https://candidates.democracyclub.org.uk/

YourNextRepresentative is a open source platform for
crowd-sourcing information about candidates for political office
and making it available as open data to anyone.

The core data that YourNextRepresentative collects includes who
is standing, what party they’re standing for, their contact
details, their social media accounts etc. The software requires
that each change is submitted with a source, so that the
collected information can be independently checked.

# Installation

See [INSTALL.md](https://github.com/DemocracyClub/yournextrepresentative/blob/master/docs/INSTALL.md)

# Known Bugs

You can find a list of known issues to work on here:

* https://github.com/DemocracyClub/yournextrepresentative/issues

# Acknowledgements

This codebase was originally forked from
[mysociety/yournextrepresentative](http://github.com/mysociety/yournextrepresentative)
We no longer track the upstream but we thank [mySociety](http://mysociety.org/)
for their work on the project which we have been able to build on.

# API Versions

v0.9 is legacy code and is now frozen. v1.0 is currently in alpha. We plan on publishing a v1 API once we have some more feedback from users and we think it’s stable enough.

# SOPN Parsing

YNR uses `pypandoc` (which relies on `pandoc`) to convert SOPN documents to PDF, as needed, to be parsed.

To install `pandoc`, visit this page and follow the instructions for you operating system:
https://pandoc.org/installing.html

Once `pandoc` is installed

Install pypandoc (or via `requirements.txt`):

`pip install pandoc`

If `pypandoc` does not install via `pip`, visit https://pypi.org/project/pypandoc/ for further instructions. 

# Sentry Error Reporting

Sentry is used to report errors in production. We have added a url for `sentry-debug` to the `urls.py` file. This is to allow us verify that Sentry is configured correctly and working in production.

```

# Pre-election Tasks

# Enable Candidate Leaderboard

The candidate leaderboard is a way of showing the most active candidates on the site. It is a way of volunteers to add more information about candidates and elections.

We take a slice of edits in YNR and assign them to a election leaderboard. 

This is defined here: https://github.com/DemocracyClub/yournextrepresentative/blob/master/ynr/apps/candidates/views/mixins.py#L20

We can modify the old value to reflect the current election. Change, PR, merge, [currently Sym needs to deploy]

If this is a General Election, the parliamentary candidates can be imported using a google sheet csv url with `python manage candidatebot_import_next_ppcs --sheet-url SHEET_URL`
