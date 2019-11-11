# Installation

TODO: improve these docs with more detail

YourNextRepresentative requires python >=3.5 and PostgreSQL

## Install python dependencies

```
pip install -r requirements.txt
```

## Set up database

```
sudo -u postgres createdb ynr
```

```
cp ynr/settings/local.py.example ynr/settings/local.py
```

Add database credentials to `DATABASES` dict in `local.py`

```
./manage.py migrate
```

## Install Front-End Dependencies

```
git submodule init
git submodule update
```

## (Optional) Code linting

A CI will check all code against Black and Flake8. To save pushing commits that don't
pass these tests you can configure pre-commmit hooks.

Do this by installing `[precommit](https://pre-commit.com/)`:

```
pip install pre-commit
pre-commit install
```

## (Optional) SOPN parsing

SOPNs parsing (see `ynr/apps/sopn_parsing/README.md`) is optional
because it depends on various system packages beyond python packages.

It currently requires [camelot-py](https://camelot-py.readthedocs.io/en/master/user/install.html#install)
and that in turn requires `python-tk` and `ghostscript`.

Read up on how to install them, and then install the SOPN parsing requirements:

```
pip install -r requirements/sopn_parsing.txt
```

## (Optional) Run automated tests

To run the test suite locally, run:

```
pytest
```

(Note that if the tests hang in `ynr/apps/bulk_adding/tests/test_bulk_add.py`
that's likely due to you not having an AMQP broker listening on
port 5672. One way of fixing this is to install RabbitMQ.)

On Travis, the tests will be run on all supported Python version
with `tox`.
