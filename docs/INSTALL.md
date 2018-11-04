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
