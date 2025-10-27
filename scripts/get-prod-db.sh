#!/bin/sh
set -euxo

# This script invokes an AWS Lambda function to retrieve a URL for downloading
# a cleaned version of the production database and then restores
# that data locally into the dbpsql container.
#
# This script requires access to the YNR production AWS account
#
# Usage:
#   ./scripts/get-prod-db.sh

# Configurable variables
LAMBDA_FUNCTION_NAME="ynr-data-exporter"

# Check for required tools
REQUIRED_TOOLS="aws dropdb createdb pg_restore curl"
for tool in $REQUIRED_TOOLS; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Error: $tool is required but not installed." >&2
    exit 1
  fi
done

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

echo "Dropping DB"
dropdb --if-exists --host 127.0.0.1 --port 54321 --username ynr ynr
echo "Creating DB"
createdb --host 127.0.0.1 --port 54321 --username ynr ynr

echo "Downloading and restoring DB"
curl --fail --silent --show-error --location "$URL" | pg_restore --dbname ynr --host 127.0.0.1 --port 54321 --username ynr --format c --no-owner --no-privileges
