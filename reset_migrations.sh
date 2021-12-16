#!/usr/bin/env bash

# exit script on an error code
set -e

# before running this script it is recommended that you take a backup of your
# local database e.g. using pg_dump -Fc ynr > ynr_backup.dump
# then if anything goes wrong you can restore easily

# ensure there are no pending migrations
python manage.py makemigrations --check --dry-run

# go through all apps and clear the migrations history in the database
for APPNAME in bulk_adding cached_counts candidates duplicates elections facebook_data frontend moderation_queue official_documents parties people popolo results search sopn_parsing twitterbot uk uk_results wombles ynr_refactoring
do
    python manage.py migrate --fake $APPNAME zero
done
