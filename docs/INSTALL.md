# Installation

## Local development

To develop YNR on the local machine you'll need to install its containerisation
prerequisites. We use containers in development to isolate the (non-trivial!)
set of *application* prerequisites away from your local machine, and to be a
bridge to the intended future state of the production application's deployment
method.

You might also need to restore a version of the YNR production data to your
local (containerised) database, depending on the type of changes you intend to
make to the application.

### Install and test containerisation prerequisites

1. Clone this repository:
   `git clone --branch jcm/wip https://github.com/DemocracyClub/yournextrepresentative`
1. Install the `podman` command: https://podman.io/docs/installation.
   These installation mechanisms have been tested:
   - System package on Ubuntu 24.04 LTS
     - https://podman.io/docs/installation#ubuntu
1. Install the `podman-compose` command: https://pypi.org/project/podman-compose/.
   These installation mechanisms have been tested:
   - System package on Ubuntu 24.04 LTS
     - This version (v1.0.x) emits non-optional verbose debug logs
     - https://packages.ubuntu.com/noble/podman-compose
     - `apt install podman-compose`
   - Manual installation of v1.2.0 APT package on Ubuntu 24.04 LTS
     - This version's verbose debug logs are optional
     - https://packages.ubuntu.com/oracular/all/podman-compose/download
     - `dkpkg -i path/to/debian-package.deb`
   - Local `pip` installation of v1.2.0 on Ubuntu 24.04 LTS
     - This version's verbose debug logs are optional
     - https://pypi.org/project/podman-compose/
     - `pip install podman-compose`
     - Either inside a venv, or not, as you prefer
1. Configure `podman` to be less chatty, by placing this configuration in `$HOME/.config/containers/containers.conf`:
   ```ini
   # Don't emit logs on each invocation of the compose command indicating
   # that an external compose provider is being executed.
   [engine]
   compose_warning_logs=false
   ```
1. Make sure the `bash` shell is available:
   `which bash || echo Not found`
1. Build any container images used by the compose stack:
   `podman compose build`
1. Pull any 3rd-party container images used by the compose stack:
   `podman compose pull`
1. Set up your local/development envvars as needed, by placing keys and values
   `env/frontend.env`, like this:
   ```
   DJANGO_SETTINGS_MODULE=ynr.settings.testing
   ```
1. Test that the compose stack can be stood up:
   ```bash
   podman compose up -d # NB Space between "podman" and "compose"!
   curl 0:8080
   ```
   Curl **should** report a server error (i.e. a 500) because your database
   setup is incomplete. This step tests only that `podman` and `podman-compose`
   are able to run successfully on your machine when given YNR's
   `docker-compose.yml` file
1. Test that Django management commands can be invoked:
   `./scripts/container.manage-py.bash check`
1. Run the test suite (which only requires that a database server be
   *available*, not that it contains any specific data). This will take a
   little time to finish:
   `./scripts/container.pytest.bash`
1. Shut down the compose stack:
   `podman compose stop`

### Restoring data

If you have access to a database dump from a YNR instance you can restore it to
a containerised database as follows:

1. Start the database container:
   `podman compose up dbpsql -d`
1. Restore the database dump:
   `cat path/to/database.dump | podman compose exec -T dbpsql pg_restore -d ynr -U ynr --no-owner`.
1. Apply any pending migrations:
   `./scripts/container.run.bash python manage.py migrate`
1. Shut down the database container:
   `podman compose down`

Now read [Running the app](#running-the-app).

<!--
Alternatively, you can populate the database using the public YNR API.
**This is significantly slower**, and will take multiple hours to complete the
`candidates_import_from_live_site` step in the following process:

FIXME: this doesn't work when run from scratch, with an entirely empty DB.
What schemas need to exist for this to work, and how are they created?

```
Importing parties from The Electoral Commission (using `parties_import_from_ec`)
Traceback (most recent call last):
  File "/dc/ynr/venv/lib/python3.8/site-packages/django/db/backends/utils.py", line 89, in _execute
    return self.cursor.execute(sql, params)
  File "/dc/ynr/venv/lib/python3.8/site-packages/psycopg/cursor.py", line 737, in execute
    raise ex.with_traceback(None)
psycopg.errors.UndefinedTable: relation "parties_party" does not exist
LINE 1: ..._party"."ec_data", "parties_party"."nations" FROM "parties_p...
                                                             ^
```

1. Start the database container:
   `podman compose up dbpsql -d`
1. Restore the database dump:
   `./scripts/container.run.bash python manage.py candidates_import_from_live_site`
1. Apply any pending migrations:
   `./scripts/container.run.bash python manage.py migrate`
1. Shut down the database container:
   `podman compose down`

-->

### Running the app

(FIXME: this will live in README.md, not INSTALL.md)

Run the app as follows:

1. Add or update any settings in `env/frontend.env` as required.
1. (Re-)Build any container images used by the compose stack:
   `podman compose build`
1. Start the compose stack:
   `podman compose up -d`
1. Build some required JS resources in the running frontend container:
   `./scripts/container.exec.bash npm run build`
1. Collect the static assets:
   `./scripts/container.manage-py.bash collectstatic --no-input`
   - FIXME: is this *only* required because we're using `gunicorn --reload`, and not `runserver`?
1. Browse to http://localhost:8080
1. Remember to shut down the compose stack when you're done:
   `podman compose down`

### Testing the app

1. Start the compose stack:
   `podman compose up -d`
1. Run the test suite, stopping on first failure:
   `./scripts/container.pytest.bash -x`
1. Stop the compose stack:
   `podman compose down`

## Setting up database

```

```
cp ynr/settings/local.py.example ynr/settings/local.py
```

Add database credentials to `DATABASES` dict in `local.py`

```
brew install libmagic
./manage.py migrate
```

## TODO

Docs TODO: **WIP!**
- static assets
- workflows for modifying different layers of the build process (NPM deps; JS and CSS; etc)
- code hot reload and its implications
