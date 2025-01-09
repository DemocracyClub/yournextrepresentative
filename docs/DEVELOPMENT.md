# Developing YNR locally

This is a guide to the tools and workflows that you'll need to use when
changing and updating YNR on your development machine.

## Installation

Install and test the development prerequisites as detailed in
[INSTALL.md](INSTALL.md). This will leave you with a known-good setup that's
able to run the commands described in this guide.

## Quick start

### Restoring data

If you have access to a database dump from a YNR instance you can restore it to
a containerised database as follows:

1. Start the database container:
   `podman compose up -d dbpsql`
1. Restore the database dump:
   ```
   cat path/to/database.dump \
   | podman compose exec -T dbpsql pg_restore -d ynr -U ynr --no-owner
   ```
1. Apply any pending migrations:
   `./scripts/container.run.bash python manage.py migrate`
1. Shut down the database container:
   `podman compose down`

<!--
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

Alternatively, you can populate the database using the public YNR API.
**This is significantly slower**, and will take multiple hours to complete the
`candidates_import_from_live_site` step in the following process:

1. Start the database container:
   `podman compose up -d dbpsql`
1. Restore the database dump:
   `./scripts/container.run.bash python manage.py candidates_import_from_live_site`
1. Apply any pending migrations:
   `./scripts/container.run.bash python manage.py migrate`
1. Shut down the database container:
   `podman compose down`
-->

### Running the app

1. Add or update any environment variables in `env/frontend.env` as required.
1. Incorporate the settings from
   [`ynr/settings/local.py.container.example`](../ynr/settings/local.py.container.example)
   into your gitignored `ynr/settings/local.py` file.
1. Start the compose stack:
   `podman compose up -d`
1. (In a separate terminal) Start tailing the stack's logs:
   `podman compose logs --follow` (you can safely CTRL-C this process at any time).
1. Build some required JS resources in the running frontend container:
   `./scripts/container.exec.bash npm run build`
1. (**If your active `ynr/settings/...` file does NOT include `DEBUG = True`**) \
   Collect the static assets:
   `./scripts/container.manage-py.bash collectstatic --no-input`
1. Browse to [http://localhost:8080](http://localhost:8080)
1. Changes made inside `ynr/` will be immediately available to the app, which
   will be auto-reloaded.
1. Remember to shut down the compose stack when you're done:
   `podman compose down`

### Testing your changes

#### If the app is capable of being started

1. Start the compose stack:
   `podman compose up -d`
1. Run the test suite:
   `./scripts/container.pytest.bash`
   - We can provide additional pytest options.
     For example, to run the test suite and stop on the first failure:
     `./scripts/container.pytest.bash -x`
1. Stop the compose stack:
   `podman compose down`

#### If the app can't be started, and you need to run the test suite to figure out why

1. Start the compose stack's database server:
   `podman compose up -d dbpsql`
1. Run the entire test suite in a new container (without starting the app):
   `./scripts/container.run.bash pytest`
1. Stop the compose stack:
   `podman compose down`

### Running Django management commands

As detailed [later in this guide](#scripts), there are several different ways
to run a command inside a frontend container.
The method described here uses a
dedicated script to invoke a Django management command inside a frontend
container that's already running the webapp.
(If you need to run a command but don't want to start the webapp, use the more
general `container.run.bash` script instead).

Run a Django management command:

1. Add or update any environment variables in `env/frontend.env` as required.
1. Start the compose stack:
   `podman compose up -d`
1. Use the `container.manage-py.bash` script to invoke the command:
   ```
   ./scripts/container.manage-py.bash command-to-invoke --command-args command params
   ```
1. Stop the compose stack:
   `podman compose down`

After you stop the compose stack, any files added or changed by the management
command inside the `ynr` directory will be persisted directly on your machine.
The same applies to any files mentioned in
[`docker-compose.yml`](../docker-compose.yml),
in the `frontend` container's "`volumes`" section.
**Any changes the management command makes to files *outside* those locations
will be lost when you stop the compose stack**.
Changes to the database are persisted in the database's data volume.

## Working with Podman

YNR uses a container runtime called [Podman](https://podman.io/). You can think
of it as like Docker, but able to run without needing a persistent background
daemon and without requiring root access.
Podman provides the `podman` command which is intended to be CLI-compatible
with much of the `docker` command.

You've also been asked to install `podman-compose` - a separate project that
gives the `podman` command its `podman compose` subcommand. You shouldn't need
to invoke `podman-compose` (with a hyphen) directly. The `podman compose`
command works with the "compose stack" defined in
[docker-compose.yml](../docker-compose.yml), which comprises two services: the
`frontend` webapp, and the Postgres `dbpsql` service.

### Working on the webapp

Use `podman compose up -d` to start the compose stack, with the webapp exposed
on [localhost:8080](http://localhost:8080). Changes you make inside the `ynr/`
directory are automatically reflected in the running app. Changes to other
entries in the frontend's [docker-compose.yml](../docker-compose.yml) list of
volumes that are bind-mounted from your local checkout of this repo are also
immediately visible to the running app.

View the app (and DB) logs with `podman compose logs --follow`. It's a good
idea to run this immediately after starting the stack.

Shut down the stack with `podman compose down`. This is always safe to run,
even when the stack is already stopped. It deliberately leaves the database's
data behind as a "volume", so that Postgres can access it the next time you
start the stack. If you need to delete the database's contents completely, run
`podman compose down --volumes`.

`podman compose ...` subcommands do provide the expected `--help` flag, but
some of the docs aren't perfect. Here's a summary of the commands you might
run:

<!-- The &nbsp; HTML entities force the Command column to be wide enough in the
GitHub-rendered view so that command strings don't line-wrap. -->
| Command&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Purpose | Notes
| :--- | :--- | :---
| `podman compose up -d` | Start the entire stack. | `-d` forks the action into the background, which is optional but strongly recommended.
| `podman compose up -d dbpsql` | Start only the named container in the stack. |
| `podman compose down` | Stop any running containers in the stack. |
| `podman compose down --volumes` | Stop any running containers in the stack and also destroy their persistent data. | Anything bind-mounted from your local repo into the `frontend` webapp container is left untouched. |
| `podman compose ps` | Display the status of containers in the stack. |
| `podman volume ls` | List the persistent volumes that podman controls on your machine. |
| `podman compose build` | Rebuild the webapp's frontend container image. |
| `podman compose build --no-cache` | Rebuild the webapp's frontend container image from scratch. | Takes several minutes to finish.
| `podman compose logs` | Display the last N stdout/stderr lines emitted by any running containers. |
| `podman compose logs --follow` | Display the last N stdout/stderr lines emitted by any running containers, and then wait for more lines. |
| `podman system reset` | Destroy everything that Podman controls. | "Everything seems to have gone wrong, so I'll just start from scratch". It wipes out all containers, networks, images, volumes, etc ... so **avoid this if possible!** |

### Scripts

These executable scripts are available from the [`scripts`](../scripts) directory.

<!-- The &nbsp; HTML entities force the Script column to be wide enough in the
GitHub-rendered view so that command strings don't line-wrap. -->
| Script | Purpose | Parameters
| :--- | :--- | :---
| `container.image.build.bash` | Builds the YNR container image | $1 -- The named stage from [`container/build/Containerfile`](../container/build/Containerfile) to build and tag (*required*)<br>$2, $3, ... -- Any parameters to pass to the underlying builder process (*optional*)
| `container.exec.bash` | Runs a command inside the already-running `frontend` container | The unquoted command to run (*required*)
| `container.manage-py.bash` | Runs a Django management command inside the already-running `frontend` container | The unquoted command to run (*required*)
| `container.pytest.bash` | Runs `pytest` inside the already-running `frontend` container | Any parameters for Pytest (*optional*)
| `container.run.bash` | Runs a command inside a freshly-instantiated, ephemeral `frontend` container | The unquoted command to run (*required*)

### Rebuilding the application container image

You will need to rebuild the application's container image if you change any of
the application's dependencies, across any of the packaging ecosystems it
currently relies on:

- `container/build/system-packages`: System / APT dependendencies
- `package{,-lock}.json`: Node dependencies
- `requirements/*.txt`: Python dependencies
- `.dockerignore`: Container build-time file dependencies

The above list is presented in descending order of how slow a rebuild will be,
if a particular package ecosystem's dependencies are changed.
Changing a system dependency, for example, forces a longer rebuild than
changing a Python dependency.
**You do not need to rebuild the application's container image if you only
change files in the `ynr/` directory**. Changes to the YNR application are
picked up automatically when using the compose stack locally (as described
elsewhere in this guide).

The build process for the YNR application is encoded in
[`container/build/Containerfile`](../container/build/Containerfile).
This Docker-compatible file describes two image stages, `prod` and `test`, with
`test` being built on top of `prod`.
Locally, on your development machine, you will need to use the `test` stage.

#### Build the `test` stage using a build cache

```
./scripts/container.image.build.bash test
```

#### Build the `test` stage without a build cache

Avoiding the use of your local build cache significantly increases the time it
takes to build the container image, but is sometimes useful when there's a
problem with external dependencies (e.g. if a important update has been
published for an APT package but it's not visible in the container's package
index).

```
./scripts/container.image.build.bash test --no-cache
```
