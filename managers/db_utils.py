import sqlite3
import psycopg2
import json
import os
import logging

def generate_insert_sql(table_name=None, columns = [], values = [], backend="sqlite"):

    if not table_name or values == []:
        return None

    if columns != []:
        columns = '(' + ", ".join(columns) + ')'
    # Choose placeholders
    if backend == "postgres":
        placeholders = ", ".join(["%s"] * len(values))
    else:  # Default to sqlite
        placeholders = ", ".join(["?"] * len(values))

    command = f"INSERT INTO {table_name} {columns} VALUES ({placeholders});"
    return command, tuple(values)





def get_db_connection(db_path=None, backend=None):
    """
    Open a database connection based on the DB_BACKEND environment variable.

    Usage:
        connection = get_db_connection()
        # connection is either an SQLite or PostgreSQL connection object.

    Environment Variables:
        DB_BACKEND (str): "sqlite" or "postgres"

    For PostgreSQL
        DB_HOST (str): Host of the PostgreSQL server
        DB_PORT (str): Port number for PostgreSQL
        DB_NAME (str): Database name
        DB_USER (str): Username
        DB_PASSWORD (str): Password

    Returns:
        A connection object for the selected database backend.
    """


    if backend == "postgres":
        print("Using PostgreSQL database")
        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=os.getenv("DB_PORT", "5432"),
                dbname=os.getenv("DB_NAME", "DWS_db"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "secret")
            )
            conn.autocommit = True
            return conn
        except Exception as e:
            print("Unable to connect to PostgreSQL database")
            raise e

    elif backend == "sqlite":
        print("Using SQLite database")
        if db_path:
            connection = sqlite3.connect(db_path)
        else:
            connection = sqlite3.connect("DWS_scraper.db")
        return connection
    else:
        print(f"Unknown DB_BACKEND='{backend}', defaulting to SQLite file='DWS_scraper.db'")
        try:
            connection = sqlite3.connect("DWS_scraper.db")
            return connection
        except Exception as e:
            print("Unable to connect to SQLite database")
