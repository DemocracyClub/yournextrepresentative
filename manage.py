#!/usr/bin/env python
import os
import sys

import dotenv
from django.core.exceptions import ImproperlyConfigured

if __name__ == "__main__":
    dotenv.load_dotenv()

    if not os.environ.get("DJANGO_SETTINGS_MODULE"):
        raise ImproperlyConfigured(
            "You must explicitly set DJANGO_SETTINGS_MODULE"
        )

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
