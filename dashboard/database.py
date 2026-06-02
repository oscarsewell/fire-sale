"""Database connection helper for Hardware Hound."""
import json
import logging
import os
from contextlib import contextmanager

import boto3
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def get_db_credentials() -> dict:
    """Load DB credentials from env vars, falling back to AWS Secrets Manager."""
    host = os.getenv("DB_HOST")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    port = os.getenv("DB_PORT")
    dbname = os.getenv("DB_NAME")

    if all([host, user, password, port, dbname]):
        logger.debug(
            "DB credentials loaded from environment variables (host=%s, dbname=%s)", host, dbname)
        return {
            "host": host,
            "port": int(port),
            "username": user,
            "password": password,
            "dbname": dbname,
        }

    secret_arn = os.getenv("DB_SECRET_ARN")
    if not secret_arn:
        logger.error(
            "DB credentials missing: no env vars and no DB_SECRET_ARN set. "
            "Set DB_HOST, DB_USER, DB_PASSWORD, DB_PORT, DB_NAME or DB_SECRET_ARN."
        )
        raise ValueError(
            "Database credentials not found. Set DB_HOST, DB_USER, DB_PASSWORD, "
            "DB_PORT, DB_NAME or set DB_SECRET_ARN for AWS Secrets Manager."
        )

    logger.info(
        "Fetching DB credentials from Secrets Manager (arn=%s)", secret_arn)
    try:
        response = boto3.client(
            "secretsmanager").get_secret_value(SecretId=secret_arn)
    except Exception as exc:
        logger.error("Failed to retrieve secret from Secrets Manager: %s", exc)
        raise
    credentials = json.loads(response["SecretString"])
    logger.debug("DB credentials loaded from Secrets Manager")
    return {
        "host": credentials["host"],
        "port": int(credentials.get("port", 5432)),
        "username": credentials["username"],
        "password": credentials["password"],
        "dbname": credentials["dbname"],
    }


@contextmanager
def get_db():
    """Context manager yielding a psycopg2 connection.

    Commits on success, rolls back on error, and always closes the connection.
    """
    creds = get_db_credentials()
    logger.debug("Opening DB connection to %s:%s/%s",
                 creds["host"], creds["port"], creds["dbname"])
    try:
        conn = psycopg2.connect(
            host=creds["host"],
            port=creds["port"],
            user=creds["username"],
            password=creds["password"],
            dbname=creds["dbname"],
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
    except psycopg2.OperationalError as exc:
        logger.error("Could not connect to database: %s", exc)
        raise
    try:
        yield conn
        conn.commit()
        logger.debug("DB transaction committed")
    except Exception as exc:
        conn.rollback()
        logger.error("DB transaction rolled back due to error: %s", exc)
        raise
    finally:
        conn.close()
        logger.debug("DB connection closed")
