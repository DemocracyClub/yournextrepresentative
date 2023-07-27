class FuzzyInt(int):
    def __new__(cls, lowest, highest):
        obj = super(FuzzyInt, cls).__new__(cls, highest)
        obj.lowest = lowest
        obj.highest = highest
        return obj

    def __eq__(self, other):
        return self.lowest <= other <= self.highest

    def __repr__(self):
        return "[%d..%d]" % (self.lowest, self.highest)


def deep_sort(obj):
    """
    Recursively sort list or dict nested lists

    Thanks to https://stackoverflow.com/questions/18464095/how-to-achieve-assertdictequal-with-assertsequenceequal-applied-to-values#27949519
    """

    if isinstance(obj, dict):
        _sorted = {}
        for key in sorted(obj):
            _sorted[key] = deep_sort(obj[key])

    elif isinstance(obj, list):
        sort_key = None
        new_list = []
        for val in obj:
            new_list.append(deep_sort(val))
            if isinstance(val, dict):
                sort_key = sorted(val)[0]
        _sorted = sorted(new_list, key=lambda k: k[sort_key])

    else:
        _sorted = obj

    return _sorted
