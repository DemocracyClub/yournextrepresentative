import uuid

from candidates.management.images import get_file_md5sum
from candidates.models import PersonRedirect
from django.core.files import File
from django.db import connection, models
from ynr_refactoring.settings import PersonIdentifierFields


class PersonImageManager(models.Manager):
    def create_from_file(self, filename, defaults, new_filename=None):
        new_filename = new_filename or f"{uuid.uuid4()}.png"
        defaults["md5sum"] = get_file_md5sum(filename)
        person_image = self.model(**defaults)
        with open(filename, "rb") as f:
            file = File(f)
            person_image.image.save(new_filename, file)
        return person_image


class PersonIdentifierQuerySet(models.query.QuerySet):
    def select_choices(self):
        default_option = [(None, "")]
        options = [(f.name, f.value) for f in PersonIdentifierFields]
        return default_option + options

    def editable_value_types(self):
        """
        Until we have a way to truly manage any key/value pair there are some
        IDs that we don't want to be user editable just yet.

        In that case, we need a way to exclude non-editable models from
        the edit form and the versions diff.
        """
        return self.filter(
            value_type__in=[vt[0] for vt in self.select_choices()]
        )


POPULATE_NAME_SEARCH_COLUMN_SQL = """
    UPDATE people_person
    SET name_search_vector = sq.terms
    FROM (
        SELECT pp.id as id,
            ---- First and last names are weight A
            --- First Name
            setweight(to_tsvector('simple', split_part(pp.name, ' ', 1)), 'B')
            ||
            --- Last Name
            setweight(to_tsvector('simple', regexp_replace(pp.name, '^.* ', '')), 'A')
            ||
            --- Full name is weight B, further boosting first and last names, adding middle names
            setweight(to_tsvector('simple', coalesce(pp.name, '')), 'C')
            ||
            --- Other names are weight C
            setweight(to_tsvector('simple', coalesce(string_agg(ppon.name, ' '), '')), 'D') as terms
        FROM people_person pp
        LEFT JOIN popolo_othername ppon
        ON pp.id = ppon.object_id
        WHERE ppon.content_type_id = (
            select id
            from django_content_type
            where app_label='people'
              and model='person')
        GROUP BY pp.id, pp.name
    ) as sq
    where sq.id = people_person.id
"""

NAME_SEARCH_TRIGGER_SQL = """
    DROP FUNCTION IF EXISTS people_person_search_trigger() CASCADE;
    CREATE FUNCTION people_person_search_trigger() RETURNS trigger AS $$
    begin
        new.name_search_vector := (
            WITH po_names as (
                select array_to_string(
                               array(
                                       select po.name
                                       from popolo_othername po
                                       where po.object_id = new.id
                                       and po.content_type_id = (
                                        select id
                                        from django_content_type
                                        where app_label='people'
                                          and model='person')
                                   ), ','
                           ) as other_names
            )
            SELECT
            setweight(to_tsvector('simple', split_part(new.name, ' ', 1)), 'B')
            ||
            --- Last Name
            setweight(to_tsvector('simple', regexp_replace(new.name, '^.* ', '')), 'A')
            ||
            --- Full name is weight B, further boosting first and last names, adding middle names
            setweight(to_tsvector('simple', coalesce(new.name, '')), 'C')
            ||
            --- Other names are weight C
            setweight(to_tsvector('simple', coalesce(string_agg(po_names.other_names, ' '), '')), 'D') as terms
            FROM po_names
        );
      return new;
    end
    $$ LANGUAGE plpgsql;
    DROP TRIGGER IF EXISTS tsvectorupdate ON people_person CASCADE;
    CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
        ON people_person FOR EACH ROW EXECUTE PROCEDURE people_person_search_trigger();
"""


class PersonQuerySet(models.query.QuerySet):
    def alive_now(self):
        return self.filter(death_date="")

    def get_by_id_with_redirects(self, person_id):
        try:
            person = self.get(id=person_id)
        except self.model.DoesNotExist:
            try:
                person_id = PersonRedirect.objects.get(
                    old_person_id=person_id
                ).new_person_id
                return self.get_by_id_with_redirects(person_id)
            except PersonRedirect.DoesNotExist:
                raise self.model.DoesNotExist
        return person

    def _run_sql(self, SQL):
        with connection.cursor() as cursor:
            cursor.execute(SQL)

    def update_name_search(self):
        self._run_sql(POPULATE_NAME_SEARCH_COLUMN_SQL)

    def update_name_search_trigger(self):
        self._run_sql(NAME_SEARCH_TRIGGER_SQL)
