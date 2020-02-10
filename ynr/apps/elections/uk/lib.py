import re


def is_valid_postcode(postcode):
    outcode_pattern = "[A-PR-UWYZ]([0-9]{1,2}|([A-HIK-Y][0-9](|[0-9]|[ABEHMNPRVWXY]))|[0-9][A-HJKSTUW])"
    incode_pattern = "[0-9][ABD-HJLNP-UW-Z]{2}"
    postcode_regex = re.compile(
        r"^(GIR 0AA|{} {})$".format(outcode_pattern, incode_pattern)
    )
    space_regex = re.compile(r" *(%s)$" % incode_pattern)

    postcode = postcode.upper().strip()

    postcode = space_regex.sub(r" \1", postcode)
    if not postcode_regex.search(postcode):
        return False
    return True
