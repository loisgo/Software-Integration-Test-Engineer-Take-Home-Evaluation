# conftest.py
import os
import pyodbc
import pytest
import time

# Database connection string configuration
DB_NAME = "MySalesDb"
CONN_STR_MASTER = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=localhost,14333;"
    "Database=master;"
    "UID=sa;"
    "PWD=YourStrong@Passw0rd;"
    "Encrypt=no;"
)

@pytest.fixture(scope="session")
def db_connection():
    # wait for SQL container to be fully ready (CI runs need this)
    retries = 20
    while retries > 0:
        try:
            conn = pyodbc.connect(CONN_STR_MASTER)
            break
        except Exception:
            time.sleep(3)
            retries -= 1
    assert retries > 0, "SQL Server did not start in time"

    # create DB if not exists
    cur = conn.cursor()
    cur.execute(f"IF DB_ID('{DB_NAME}') IS NULL CREATE DATABASE {DB_NAME}")
    conn.commit()

    # connect to the test DB itself
    CONN_STR_TEST = (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server=localhost,14333;"
        f"Database={DB_NAME};"
        "UID=sa;"
        "PWD=YourStrong@Passw0rd;"
        "Encrypt=no;"
    )
    test_conn = pyodbc.connect(CONN_STR_TEST)

    # load schema
    schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "schema.sql"))
    with open(schema_path, "r") as f:
        sql = f.read()

    cur2 = test_conn.cursor()
    cur2.execute(sql)
    test_conn.commit()

    yield test_conn

    # teardown drop database
    test_conn.close()
    cur.execute(f"ALTER DATABASE {DB_NAME} SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
    cur.execute(f"DROP DATABASE {DB_NAME}")
    conn.commit()
    conn.close()
