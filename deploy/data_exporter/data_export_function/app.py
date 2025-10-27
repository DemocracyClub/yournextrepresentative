import os
import subprocess
from datetime import datetime, timedelta, timezone

import boto3
import psycopg
from psycopg import sql

ssm = boto3.client("ssm")
s3 = boto3.client("s3", region_name="eu-west-1")
BUCKET_NAME = "ynr-short-term-backups-production"
PREFIX = "ynr-export"
FILENAME_FORMAT = "{PREFIX}-{CURRENT_TIME_STR}.dump"


def get_parameter(name):
    response = ssm.get_parameter(Name=name)
    return response["Parameter"]["Value"]


SOURCE_DATABASE = get_parameter("/POSTGRES_DBNAME")
TMP_DATABASE_NAME = "ynr-for-dev-export"
DB_HOST = get_parameter("/POSTGRES_HOST")
DB_USER = get_parameter("/POSTGRES_USERNAME")
DB_PASSWORD = get_parameter("/POSTGRES_PASSWORD")
DB_PORT = "5432"
os.environ["PGPASSWORD"] = DB_PASSWORD


def get_db_conn(db_name):
    conn = psycopg.connect(
        dbname=db_name,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )
    conn.autocommit = True
    return conn


def create_database_and_restore():
    conn = get_db_conn(SOURCE_DATABASE)
    try:
        with conn.cursor() as cur:
            print(f"Deleting {TMP_DATABASE_NAME}")
            cur.execute(
                sql.SQL("DROP DATABASE IF EXISTS {};").format(
                    sql.Identifier(TMP_DATABASE_NAME)
                )
            )
        with conn.cursor() as cur:
            # SQL to create the new database from the source
            print(f"Creating {TMP_DATABASE_NAME}")
            cur.execute(
                sql.SQL("CREATE DATABASE {} ;").format(
                    sql.Identifier(TMP_DATABASE_NAME),
                )
            )
            print(
                f"Database '{TMP_DATABASE_NAME}' created successfully '{SOURCE_DATABASE}'."
            )
    except psycopg.Error as e:
        print(f"Error creating database: {e}")
        raise

    finally:
        conn.close()

    # Dump and restore the source DB to the temp one
    dump_command = [
        "pg_dump",
        "-h",
        DB_HOST,
        "-U",
        DB_USER,
        "-d",
        SOURCE_DATABASE,
        "-Fc",
    ]

    restore_command = [
        "pg_restore",
        "-h",
        DB_HOST,
        "-U",
        DB_USER,
        "-d",
        TMP_DATABASE_NAME,
    ]

    print("Populating new database (pg_dump | pg_restore")
    with subprocess.Popen(
        dump_command,
        stdout=subprocess.PIPE,
    ) as dump_proc:
        subprocess.run(
            restore_command,
            stdin=dump_proc.stdout,
            check=True,
        )
        dump_proc.stdout.close()


def clean_database():
    conn = get_db_conn(db_name=TMP_DATABASE_NAME)
    with conn.cursor() as cur:
        print("Cleaning Users table")
        cur.execute(
            """UPDATE auth_user SET 
                email = CONCAT('anon_', id, '@example.com'), 
                password = md5(random()::text);
            """
        )
        print("Cleaning Account email table")
        cur.execute(
            """UPDATE account_emailaddress SET 
                email = CONCAT('anon_', id, '@example.com');
            """
        )
        print("Cleaning IP addresses from LoggedActions")
        cur.execute(
            """UPDATE candidates_loggedaction SET 
                ip_address = '127.0.0.1';
            """
        )
        print("Cleaning API tokens")
        cur.execute(
            """UPDATE authtoken_token SET 
                key = md5(random()::text);
            """
        )
        print("Cleaning sessions")
        cur.execute("""TRUNCATE TABLE django_session;""")


def get_filename():
    return FILENAME_FORMAT.format(
        PREFIX=PREFIX, CURRENT_TIME=datetime.now().isoformat().replace(":", "-")
    )


def dump_and_export():
    dump_file = "/tmp/db_dump.sql"  # Temporary file for the dump

    print("Run pg_dump to create the database dump")
    try:
        subprocess.run(
            [
                "pg_dump",
                "-h",
                DB_HOST,
                "-U",
                DB_USER,
                "-d",
                TMP_DATABASE_NAME,
                "-Fc",
                "-f",
                dump_file,
            ],
            check=True,
        )

        file_name = get_filename()

        print("Upload the dump to S3")
        s3.upload_file(dump_file, BUCKET_NAME, file_name)

        print("Generate a presigned URL for downloading the dump")
        presigned_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET_NAME, "Key": file_name},
            ExpiresIn=3600,  # URL expires in 1 hour
        )
        print("Finished")
        return presigned_url

    except subprocess.CalledProcessError as e:
        return f"Error generating database dump: {str(e)}"


def check_for_recent_exports():
    """
    If we've exported a file in the last hour, don't export another one

    """
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=PREFIX)
    if "Contents" in response:
        recent_files = [
            obj
            for obj in response["Contents"]
            if obj["LastModified"] >= one_hour_ago
        ]

        recent_files.sort(key=lambda obj: obj["LastModified"], reverse=True)

        if recent_files:
            return s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": BUCKET_NAME, "Key": recent_files[0]["Key"]},
                ExpiresIn=3600,  # URL expires in 1 hour
            )
    return None


def lambda_handler(event, context):
    if recent_export := check_for_recent_exports():
        return recent_export

    print("Creating temp database")
    create_database_and_restore()
    print("Cleaning temp database")
    clean_database()
    print("Dumping and exporting")
    return dump_and_export()
