#!/bin/sh
set -euxo

# This script invokes an AWS Lambda function to retrieve a URL for downloading
# a cleaned version of the production database and then restores
# that data locally. By default the db name is "ynr-prod" but you can change the
# local name by passing it as the first argument to the script.
#
# This script requires access to the YNR production AWS account
#
# Usage:
#   ./scripts/get-prod-db.sh [LOCAL_DB_NAME]
#
# Arguments:
#   LOCAL_DB_NAME: Optional. Name of the local database to restore data to.
#                  Defaults to 'ynr-prod' if not specified.

# Configurable variables
LAMBDA_FUNCTION_NAME="ynr-data-exporter"
LOCAL_DB_NAME="${1:-ynr-prod}"

# Check for required tools
REQUIRED_TOOLS="aws dropdb createdb pg_restore wget"
for tool in $REQUIRED_TOOLS; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Error: $tool is required but not installed." >&2
    exit 1
  fi
done

# Check the DB URL and get the cleaned $_SCRIPT_DATABASE_URL
. ./scripts/check-database-url.sh


# Create a temporary file and set up clean up on script exit
TEMP_FILE=$(mktemp)
trap 'rm -f "$TEMP_FILE"' EXIT

# Invoke AWS Lambda and store the result in the temp file
# The result is a pre-signed URL to the dump file on S3
echo "Invoking Lambda to get DB URL. This might take a few minutes..."
aws lambda invoke \
  --function-name "$LAMBDA_FUNCTION_NAME" \
  --cli-read-timeout=0 \
  --no-cli-pager \
  --output text \
  --query 'Payload' \
  "$TEMP_FILE"

# Extract the URL from the response
# This is because the response is quoted, so we just need to remove the quotation marks
URL=$(sed 's/^"\(.*\)"$/\1/' "$TEMP_FILE")
case "$URL" in
    https://*)
        echo "Got URL: $(URL)"

        ;;
    *)
        echo "The received URL looks invalid. This might mean the database export failed."
        echo "Check the logs of the '$LAMBDA_FUNCTION_NAME' Lambda function"
        exit 1
        ;;
esac

echo "Dropping DB $(_SCRIPT_DATABASE_URL)"
dropdb --if-exists "$_SCRIPT_DATABASE_URL"
echo "Creating DB $(_SCRIPT_DATABASE_URL)"
createdb "$_SCRIPT_DATABASE_URL"

echo "Downloading and restoring DB $(_SCRIPT_DATABASE_URL)"
wget -qO- "$URL" | pg_restore -d "$_SCRIPT_DATABASE_URL" -Fc --no-owner --no-privileges
