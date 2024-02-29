import csv
import io


class BufferDictReader(csv.DictReader):
    r"""A DictReader to work with streams, automating the selection of a buffer.

    >>> reader = BufferDictReader(b'α,b,c\r\n1,2,\r\n')
    >>> tuple(reader) == ({u'α': u'1', u'b': u'2', u'c': u''},)
    True
    """

    def __new__(
        cls,
        s=b"",
        fieldnames=None,
        restkey=None,
        restval=None,
        dialect="excel",
        *_,
        **kwargs,
    ):
        s = io.StringIO(s.decode("utf-8"))
        return csv.DictReader(
            s, fieldnames, restkey, restval, dialect, **kwargs
        )


class BufferDictWriter(csv.DictWriter):
    r"""A DictWriter to work with streams, automating the selection of a buffer.

    >>> writer = BufferDictWriter((u'α', u'b', u'c'))
    >>> writer.writeheader()
    >>> _ = writer.writerow({u'α': 1, u'b': 2})
    >>> writer.output == u'α,b,c\r\n1,2,\r\n'
    True
    """

    def __init__(
        self,
        fieldnames,
        restval="",
        extrasaction="raise",
        dialect="excel",
        *_,
        **kwargs,
    ):
        self.f = io.StringIO()
        super().__init__(
            self.f, fieldnames, restval, extrasaction, dialect, **kwargs
        )

    @property
    def output(self):
        return self.f.getvalue()
