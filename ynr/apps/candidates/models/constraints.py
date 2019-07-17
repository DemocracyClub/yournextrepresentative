def check_no_candidancy_for_election(person, election):
    if election.ballot_set.filter(
        membership__person=person,
        membership__role=election.candidate_membership_role,
    ).exists():
        msg = (
            "There was an existing candidacy for {person} ({person_id}) "
            'in the election "{election}"'
        )
        raise Exception(
            msg.format(
                person=person, person_id=person.id, election=election.name
            )
        )
