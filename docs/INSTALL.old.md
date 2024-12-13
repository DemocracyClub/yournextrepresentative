# Installation

TODO: improve these docs with more detail

YourNextRepresentative requires python >=3.5 and PostgreSQL

## Install python dependencies

```
pip install -U pip
pip install -r requirements.txt
```

## Set up database

```
sudo -u postgres createdb ynr
```

If using mac-os/homebrew
```
createdb ynr
```

```
cp ynr/settings/local.py.example ynr/settings/local.py
```

Add database credentials to `DATABASES` dict in `local.py`

```
brew install libmagic
./manage.py migrate
```

To populate the database run from the live site run:

```
python manage.py candidates_import_from_live_site
```

(Note that this command will take multiple hours to complete.)

## Build frontend assets

```
npm run build
npm install
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

File conversion relies on `pandoc` to turn non-pdf SOPN files into pdf files.
To install `pandoc`, visit https://pandoc.org/installing.html and follow instructions
for Mac OS and Ubuntu.

AWS Textract relies on the following packages for viewing image results: 

https://pypi.org/project/pdf2image/

To install these packages run:

```
brew install poppler
```

_If you have omitted SOPN and are having problems getting the project to run, you may need to follow the SOPN steps._