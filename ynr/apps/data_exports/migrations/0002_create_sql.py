"""
The SQL to create a materialized view containing a row per membership
(candidacy)

Use crosstab to create a column for each PersonIdentifier value type.

The values types need to be created dynamically as postgres offers
no way to use populate the columns from the value types itself.

"""

from django.db import migrations

SQL_STR = """
DROP MATERIALIZED VIEW IF EXISTS materialized_memberships;
CREATE MATERIALIZED VIEW materialized_memberships AS
SELECT
    mem.id as id,
    ballots.ballot_paper_id,
    Cast(position('.by.' in ballot_paper_id) as BOOLEAN) as is_by_election,
    ballots.election_name,
    ballots.election_date,
    ballots.post_label as division_name,
    mem.person_id,
    mem.party_list_position,
    person.name as person_name,
    parties.ec_id as party_id,
    parties.name as party_name,
    mem.elected,
    person_ids.json_data as identifiers
FROM popolo_membership as mem
JOIN people_person person on mem.person_id = person.id
JOIN (
    SELECT
        _ballots.id as ballot_id,
        elections.name as election_name,
        elections.election_date as election_date,
        posts.label as post_label,
        _ballots.*
    FROM candidates_ballot as _ballots
    JOIN elections_election as elections
    ON elections.id = _ballots.election_id
    JOIN popolo_post posts
    ON _ballots.post_id = posts.id
) as ballots
ON mem.ballot_id = ballots.ballot_id
JOIN parties_party as parties
ON mem.party_id = parties.id

LEFT JOIN (

    SELECT p.id as person_id, json_ids as json_data
    FROM people_person p
    JOIN (
        SELECT person_id, json_object_agg(
        src.value_type, src.value
    )::jsonb AS json_ids
    FROM (
        SELECT person_id, value_type, value
        FROM people_personidentifier
        GROUP BY person_id, value_type, value
    ) src

   GROUP BY person_id
   ) src_json
   ON p.id = src_json.person_id



)
AS person_ids
ON person_ids.person_id=person.id
ORDER BY mem.person_id
        """


class Migration(migrations.Migration):
    dependencies = [("data_exports", "0001_initial")]

    operations = [migrations.RunSQL(SQL_STR)]
