import os
import subprocess
from datetime import datetime, timedelta, timezone

import boto3
import psycopg
from psycopg import sql

ssm = boto3.client("ssm")
s3 = boto3.client("s3", region_name="eu-west-1")
bucket_name = "dc-ynr-short-term-backups"
current_time = datetime.now().isoformat()
PREFIX = "ynr-export"
FILENAME = f"{PREFIX}-{current_time.replace(':', '-')}.dump"


def get_parameter(name):
    response = ssm.get_parameter(Name=name)
    return response["Parameter"]["Value"]


SOURCE_DATABASE = "ynr"
TMP_DATABASE_NAME = "ynr-for-dev-export"
DB_HOST = get_parameter("/ynr/production/POSTGRES_HOST")
DB_USER = get_parameter("/ynr/production/POSTGRES_USERNAME")
DB_PASSWORD = get_parameter("/ynr/production/POSTGRES_PASSWORD")
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


def create_database_from_template():
    # Connect to the PostgreSQL server (usually to the 'postgres' database for administrative tasks)
    conn = get_db_conn(SOURCE_DATABASE)
    # Enable autocommit to run CREATE DATABASE commands
    try:
        with conn.cursor() as cur:
            print(f"Deleting {TMP_DATABASE_NAME}")
            cur.execute(
                sql.SQL("DROP DATABASE IF EXISTS {};").format(
                    sql.Identifier(TMP_DATABASE_NAME)
                )
            )
        with conn.cursor() as cur:
            # SQL to create the new database from the template
            print(f"Creating {TMP_DATABASE_NAME}")
            cur.execute(
                sql.SQL("CREATE DATABASE {} TEMPLATE {};").format(
                    sql.Identifier(TMP_DATABASE_NAME),
                    sql.Identifier(SOURCE_DATABASE),
                )
            )
            print(
                f"Database '{TMP_DATABASE_NAME}' created successfully from template '{SOURCE_DATABASE}'."
            )
    except psycopg.Error as e:
        print(f"Error creating database: {e}")
    finally:
        conn.close()


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
            """UPDATE auth_user SET 
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


def dump_and_export():
    dump_file = "/tmp/db_dump.sql"  # Temporary file for the dump

    # Database credentials and parameters

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

        print("Upload the dump to S3")
        s3.upload_file(dump_file, bucket_name, FILENAME)

        print("Generate a presigned URL for downloading the dump")
        presigned_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": FILENAME},
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
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=PREFIX)
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
                Params={"Bucket": bucket_name, "Key": recent_files[0]["Key"]},
                ExpiresIn=3600,  # URL expires in 1 hour
            )
    return None


def lambda_handler(event, context):
    if recent_export := check_for_recent_exports():
        return recent_export

    print("Creating temp database")
    create_database_from_template()
    print("Cleaning temp database")
    clean_database()
    print("Dumping and exporting")
    return dump_and_export()
