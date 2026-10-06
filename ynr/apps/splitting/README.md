# Splitting

Moves a candidacy that has ended up on the wrong person to the right one.
This is roughly the inverse of merging (`people/merging.py`).

Candidacies end up on the wrong person in two ways:

1. Two different people were merged.
2. A candidacy was added to the wrong existing person, usually when adding
   candidates from a SOPN. This is the more common case.

## Using it

### Website

Users in the "Trusted to split" group (`models.TRUSTED_TO_SPLIT_GROUP_NAME`,
created by a migration) see a "Split person" button on the page of any
person with more than one candidacy. It's a separate group from "Trusted To
Merge" so splitting can be rolled out to a few users first. The split page
asks for:

- **Candidacy to move**
- **Destination person ID**: `new`, or the ID of the person the candidacy
  belongs to (a person URL works too)

"Preview" shows a one-line summary with any errors and warnings. Nothing
changes until "Split" is pressed. Warnings have to be ticked first, and the
split is refused if the choices or the person have changed since the
preview. "Details and options" shows where the candidacy came from, where
each detail will go (with per-detail overrides), and options.

Moving candidacies on locked ballots is allowed on the website, but shown as
a warning.

### Management command

```
python manage.py splitting_split_person <person_id> <ballot_paper_id> [--to-person ID] [--suggest] [--commit]
```

Without `--commit` it only shows what would happen. It prints one
tab-separated row (Person URL, Person ID, Ballot, Destination person ID,
Result, Notes) for pasting into a tracking sheet. Other options:

- `--suggest`: work out where the candidacy came from and what else to move
  (always on for `new` on the website)
- `--allow-locked`: allow changing locked ballots
- `--cutoff-days N`: only restore contact details, links and biographies
  changed in the last N days (default 365)
- `--move-field FIELD` / `--keep-field FIELD`: override a suggestion
- `--move-image`: move the person's photo too
- `--details`: show the full plan
- `--no-header`: leave out the header row
- `--username`: the user to record the split against

## How it works

`splitter.PersonSplitter` works in two steps. `plan()` returns a `SplitPlan`
describing the changes, warnings and errors without changing anything.
`split()` applies it in one transaction.

The `Membership` itself is moved, so the result, elected status, list
position, previous party affiliations and SOPN names go with it. Result
events move too. Both people get a new version and a logged action: the
original person a `person-split`, and the other person a `person-create`
(new or restored) or `candidacy-create` (existing person).

With suggestions on, `provenance.find_origin()` reads the person's version
history to find where the candidacy was added:

- **From a merge**: the merged-away person is restored under their old ID
  if it's free, with their other candidacies, their version history and
  logged actions, and the redirect from their old ID is deleted. Details are
  divided between the two people from each person's last version before the
  merge, undoing what `PersonMerger` did.
- **Added directly**: details changed in the same edit as the candidacy
  (usually the SOPN name, or a rename) move with it.

Details edited after the candidacy arrived are marked for checking and stay
on the original person unless overridden.

## Limits

- Suggestions can't be combined with moving to an existing person, as they
  would overwrite that person's details.
- If a merged-away person's old ID can't be reused, they get a new ID and
  their version history isn't copied, because the versions page can't show
  history that belongs to a different ID.
- The original person keeps the merged-away person's versions and the merge
  version in their history. Removing only some of them would break their
  versions page.
- Some things a merge does can't be undone: a photo deleted because both
  people had one, and two candidacies on the same ballot combined into one.

## Tests

- `test_provenance.py`: origin detection and suggestions, on hand-built
  version histories (no database)
- `test_splitting.py`, `test_splitting_suggest.py`: the splitter and the
  command
- `test_split_view.py`: the web page
- `test_merge_split_round_trip.py`: merging two people and splitting them
  again through the website leaves both exactly as they were
