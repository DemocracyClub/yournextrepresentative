# Developing YNR locally

This is a guide to the tools that you'll need to use when changing and updating
YNR on your development machine. It doesn't contain any information about the
specific kinds of code-level changes you might make - it only describes the
tools used for operating the containerised YNR setup.

## Installation

Install and test the development prerequisites as detailed in
[INSTALL.md](INSTALL.md). This will leave you with a known-good setup that's
able to run the commands described in this guide.

## Working with Podman

YNR uses a container runtime called [Podman](https://podman.io/). You can think
of it as like Docker, but able to run without needing a persistent background
daemon and without requiring root access. It provides a `podman` command which
is intended to be CLI-compatible with the `docker` command.

In addition to Podman, the installation steps linked above also ask you to
install `podman-compose` - a separate project that gives the `podman` command
its `podman compose` subcommand. You shouldn't need to invoke `podman-compose`
(with a hyphen) directly. The compose command works with the "compose stack"
defined in [docker-compose.yml](../docker-compose.yml), which comprises two
services: the `frontend` webapp, and the Postgres `dbpsql` service.

### Working on the webapp

Use `podman compose up -d` to start the compose stack, with the webapp exposed
on [localhost:8080](http://localhost:8080). Changes you make inside the `ynr/`
directory are automatically reflected in the running app. Change to other
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

`podman compose ...` subcommands provide the expected `--help` flag, but some
of the docs aren't perfect. Here's a summary of the commands you might run:

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

TODO

### Rebuilding the webapp image

TODO
