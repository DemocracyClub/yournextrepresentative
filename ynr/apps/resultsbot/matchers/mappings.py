import json
import os

import resultsbot


class SavedMapping(dict):
    def __init__(self, file_name):
        self.file_name = file_name
        self.path = os.path.join(
            os.path.dirname(resultsbot.__file__),
            self.file_name
        )
        self.load()

    def load(self):
        try:
            self.update(json.loads(open(self.path).read()))
        except IOError:
            with open(self.path,'w') as f:
                f.write('{}')

    def save(self):
        with open(self.path, 'w') as f:
            f.write(json.dumps(self, indent=4, sort_keys=True))

    def picker(self, name):
        print("No match for '{}' found. Can you enter a manual match?".format(
            name
        ))
        print("This match will be saved for future in {}".format(self.path))
        match = raw_input("New name or ID: ")
        self.update({name: match})
        self.save()
        return match
