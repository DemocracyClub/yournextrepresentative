# SOPN Parsing

This app is designed to extract useful information out of UK Statement
Of Persons Nominated documents (SOPNs), published before elections.

The documents contain information on candidates for a given election,
but are published in a wide variety of layouts.

This app only deals with the majority case of the _format_ being a PDF,
but the layout and content still change a lot.

Read [the blog post about this](https://democracyclub.org.uk/blog/2018/03/12/machine-learning-help-elections/)
for more background.

At a high level this app deals with a couple of tasks:

## 1. Page discovery for a single ballot

Some SOPNs are published _per election_ (YNR election, the group
directly above ballots) with more than one ballot.

In some cases a single ballot's worth of candidates can span two pages.

The page parsing function will extract the start and end pages from a
SOPN for a given ballot.

It takes the document from the OfficialDocuments model and assumes
that duplicate source urls across different OfficialDocuments instances
indicate that more than one ballot is contained in the document.

## 2. Candidate extraction from pages

Given an PDF document and a range of pages, extract the table of
candidate names, party descriptions.
