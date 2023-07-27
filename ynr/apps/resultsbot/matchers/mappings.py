import json
import os

import resultsbot


class SavedMapping(dict):
    def __init__(self, file_name, **kwargs):
        super().__init__(**kwargs)
        self.file_name = file_name
        self.path = self._get_path()
        self.load()

    def _get_path(self):
        return os.path.join(
            os.path.dirname(resultsbot.__file__), self.file_name
        )

    def load(self):
        try:
            with open(self.path) as f:
                self.update(json.loads(f.read()))
        except (IOError, json.JSONDecodeError):
            with open(self.path, "w") as f:
                f.write("{}")

    def save(self):
        with open(self.path, "w") as f:
            f.write(json.dumps(self, indent=4, sort_keys=True))

    def picker(self, name):
        print(
            "No match for '{}' found. Can you enter a manual match?".format(
                name
            )
        )
        print("This match will be saved for future in {}".format(self.path))
        match = input("New name or ID: ")
        match = match.strip()
        self.update({name: match})
        self.save()
        return match
