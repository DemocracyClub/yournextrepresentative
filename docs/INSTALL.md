# Installation

## Local development

To develop YNR on your local machine you'll first need to install its
containerisation prerequisites. We use containers in development to isolate the
(non-trivial!) set of *application* prerequisites away from your local machine,
and to get closer to the intended future state of the application's
*production* deployment.

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
   `docker-compose.yml` file.
1. Test that Django management commands can be invoked:
   `./scripts/container.manage-py.bash check`
1. Run the test suite (which only requires that a database server be
   *available*, not that it contains any specific data).
   This will take a little time to finish:
   `./scripts/container.pytest.bash`
1. Shut down the compose stack:
   `podman compose stop`

Now you can use the tools and workflows detailed in [DEVELOPMENT.md](DEVELOPMENT.md).
