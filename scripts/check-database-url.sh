# This script does two things:
#
#  1. Gets a DATABASE_URL from the environment or the first argument and
#     normalizes it to be able to connect to postgres's CLI tools
#  2. Validates that it's possible to connect to the URL provided
#  3. Sets a validated URL as the `_SCRIPT_DATABASE_URL` environment variable for
#     use in other scripts. This only happens if the script detects it's not
#     being invoked directly.
#
# This script can be used on its own for validating connections (useful for
# debugging different environments and catching problems early) or as a
# utility script in other scripts that need to connect to a database.

REQUIRED_POSTGRES_VERSION="16"

# Check for required tools
REQUIRED_TOOLS="createdb psql"
for tool in $REQUIRED_TOOLS; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Error: $tool is required but not installed." >&2
    exit 1
  fi
done


# Get the database URL
# TODO: we might want this to be its own script
# 1. Check if DATABASE_URL is provided as the first argument
if [ -n "${1:-}" ]; then
    echo "Getting DATABASE_URL from the provided argument"
    DATABASE_URL="$1"
# 2. Check DATABASE_URL is set in the environment
elif [ -n "$DATABASE_URL" ]; then
    echo "Getting DATABASE_URL from the environment"
    DATABASE_URL="$DATABASE_URL"
fi

# Normalize if DATABASE_URL starts with "postgis://"
# We do this because `dj-database-url` uses "postgis://"
# to alter the Django engine that's used, but the postgres
# cli tools don't support this protocol.
case "$DATABASE_URL" in postgis://*)
        DATABASE_URL="postgres://${DATABASE_URL#postgis://}"
        ;;
esac

# Check if DATABASE_URL is set after all attempts
if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL is not provided."
    echo "please the environment variable DATABASE_URL or pass it in as an argument"
    echo "The format must comply with \033[4mhttps://www.postgresql.org/docs/$REQUIRED_POSTGRES_VERSION/libpq-connect.html#LIBPQ-CONNSTRING-URIS\033[0m"
    exit 1
fi

# Extract the database name from the database URL.
# 1. Use sed to remove any trailing slashes
# 2. Use `tr` to replace slashes with newlines
# 3. Use tail to get the last line, e.g the last element after a slash
# 4. Use the same method to strip off any query arguments after a `?`
DB_NAME=$(echo "$DATABASE_URL" |  sed 's:/*$::' | tr "/" "\n" | tail -n 1 | tr "?" "\n" | head -n 1)

# Create the database if it doesn't exist.
# If it already exists, we don't fail. At this point,
# we're only making a DB to ensure that we can connect to the
# database URL in the next step, so we can ignore fails here.
# Because of this, we route the output of `createdb` to /dev/null.
# Without this, the script prints an error that might confuse users
echo "Creating the DB if it doesn't exist."
createdb $DB_NAME >/dev/null 2>&1 || true

# Check that we can connect to the local DB before returning
psql $DATABASE_URL -c "\q"
if [ $? -ne 0 ]; then
  echo "❌ Failed to connect to $DATABASE_URL"
  exit 1
fi


# Check the server version
SERVER_POSTGRES_VERSION=$(psql -t -c "SHOW server_version;" -d $DATABASE_URL | cut -d '.' -f 1)
if [ $SERVER_POSTGRES_VERSION != $REQUIRED_POSTGRES_VERSION ]; then
  echo "❌ Postgres version $REQUIRED_POSTGRES_VERSION required, found $SERVER_POSTGRES_VERSION"
fi

echo "✅ Successfully connected to the local database '$DB_NAME'"


# Check if the basename of $0 (the file that was executed) is the same
# as this file name. If not, this script is being called as a 'utility'
# so we should set an environment variable.
if [ "${0##*/}" != "check-database-url.sh" ]; then
    # Script is being sourced, export a "private" DATABASE URL
    # that we can use in other scripts
    export _SCRIPT_DATABASE_URL=$DATABASE_URL
fi
