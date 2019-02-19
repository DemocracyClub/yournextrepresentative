"""
A helper to move away from SimplePopoloField and ComplexPopoloField
models.
"""


class BaseField:
    def __init__(self, *args, **kwargs):
        self.required = False

        for k, v in kwargs.items():
            setattr(self, k, v)

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name


class SimplePopoloField(BaseField):
    pass


honorific_prefix = SimplePopoloField(
    name="honorific_prefix",
    label="Title / pre-nominal honorific (e.g. Dr, Sir, etc.)",
    info_type_key="text",
    order=1,
    required=False,
)

name = SimplePopoloField(
    name="name", label="Full name", info_type_key="text", order=2, required=True
)

honorific_suffix = SimplePopoloField(
    name="honorific_suffix",
    label="Post-nominal letters (e.g. CBE, DSO, etc.)",
    info_type_key="text",
    order=3,
    required=False,
)

email = SimplePopoloField(
    name="email", label="Email", info_type_key="email", order=4, required=False
)

gender = SimplePopoloField(
    name="gender",
    label="Gender (e.g. “male”, “female”)",
    info_type_key="text",
    order=5,
    required=False,
)

birth_date = SimplePopoloField(
    name="birth_date",
    label="Date of birth (a four digit year or a full date)",
    info_type_key="text",
    order=6,
    required=False,
)

death_date = SimplePopoloField(
    name="death_date",
    label="Date of death (a four digit year or a full date)",
    info_type_key="text",
    order=7,
    required=False,
)

biography = SimplePopoloField(
    name="biography",
    label="Biography",
    info_type_key="text_multiline",
    order=10,
    required=False,
)

simple_fields = [
    honorific_prefix,
    name,
    honorific_suffix,
    gender,
    birth_date,
    death_date,
    biography,
]

simple_fields = sorted(simple_fields, key=lambda x: x.order)
