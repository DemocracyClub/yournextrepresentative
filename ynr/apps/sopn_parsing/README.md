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


## Testing SOPN parsing

There are some management commands designed to help us check that
changes we make to how SOPN's are parsed do not make things *worse* than
before. In order to easily run these easily there is a Makefile.

First, ensure you have the Textract related settings up to date in order to successfully run the following commands. These can be found in `local.py.example` and should be added to your `local.py` file. If you receive an invalid token error from AWS, it's likely that you have not updated these settings. 

The main command to use is `make test-sopns` (although see pre-requisites below before running for the first time). This will parse existing
`OfficialDocument` objects and print out results of how many were
successfully parsed.

All of the Makefile commands will load the `ynr/apps/sopn_testing.py` settings
module so as not to interfere with our local development environment. As such,
before running the `test-sopns` command for the first time you will need to take
the following steps:

- Create the `ynr_sopn_testing` database (see `INSTALL.md` for more
notes about creating databases)
- For the first time running use `make populate-sopn-testing-database`. This
will import data such as ballots from the live site that the other commands are
reliant on
- Then run `make download-sopns` which will download the SOPN pdf's and use them
to create `OfficialDocument` objects that can then be used to test against. This
command is seperated from `test-sopns` so that we can test the SOPN parsing
without making repeated unnecessary calls to the YNR api.
- When this is completed you can now use the `make test-sopns` command.

At this point an example of the intended workflow to make use of the command
would be:
- Run `make test-sopns` which will create an 'baseline' the number of SOPN's we
are currently parsing successfully
- Make some changes in the code to attempt to improve how SOPN's are parsed
- Re-run the `make test-sopns` command to check that the changes have improved
the parsing process across the same set of objects. An `AssertionError` will be
returned if the number we have been able to parse has gone down.

To download SOPN's for a specific election, open the Makefile and in the
`download-sopns` command add the election slugs to the `--election-slugs=`
argument as a comma seperated list e.g.
`--election-slugs=local.sheffield.2021-05-06,local.derbyshire.2021-05-06`.
Remember not to commit these changes in the Makefile.

To run the `make test-sopns` command for a specific Election, open the Makefile
and in the `test-sopns` command add the election slugs to the `--election-slugs=`
argument as a comma seperated list e.g.
`--election-slugs=local.sheffield.2021-05-06,local.derbyshire.2021-05-06`.
Remember not to commit these changes in the Makefile.

To run the `make test-sopns` command for a single Ballot, open the Makefile
and in the `test-sopns` command add the ballot paper id to the `--ballot=`
argument e.g. `--ballot=local.derbyshire.ilkeston-west.2021-05-06`.
Remember not to commit these changes in the Makefile.

NB you must have the relevant objects in your database and SOPN's downloaded.

To clear all downloaded SOPN's and related objects, use `make delete-test-sopns`.
This is useful if you want to rerun the testing from scratch.
