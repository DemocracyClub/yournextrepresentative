from django.db.models import Transform, Func


class LastWord(Transform):
    """
    Split a field on space and get the last element
    """

    function = "LastWord"
    template = """
    regexp_replace(%(field)s, '^.* ', '')
    """

    def __init__(self, column, output_field=None):
        super(LastWord, self).__init__(column, output_field=output_field)

    def as_postgresql(self, compiler, connection):
        return self.as_sql(compiler, connection)


class NullIfBlank(Func):
    template = "NULLIF(%(expressions)s, '')"


class Levenshtein(Func):
    """
    Uses postgres fuzzystrmatch to determine similarity between
    strings. We use when we parse table data from SOPN's to help find
    a matching Party or PartyDescription objects.
    """

    function = "levenshtein"
    arity = 2
