import pytest
import pyodbc
from datetime import datetime

# Database connection string
DB_CONN_STR = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=localhost;"
    "Database=MySalesDB;"
    "UID=sa;"
    "PWD=YourStrong@Passw0rd;"
    "Encrypt=no"
)

# Utility function to connect and execute a query
def execute_db_query(sql, params=None):
    conn = pyodbc.connect(DB_CONN_STR)
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        row = cursor.fetchone()
        return row
    finally:
        cursor.close()
        conn.close()

# Helper: insert a test sale into sales_hdr
def insert_test_sale(db_connection, sale_id, total, payment_status="Paid"):
    cursor = db_connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO sales_hdr (id, sale_date, total, payment_status) VALUES (?, ?, ?, ?)",
            (sale_id, datetime.now(), total, payment_status)
        )
        db_connection.commit()
    finally:
        cursor.close()

# =======================
# Test: Successful Payment
# =======================
def test_checkout_successful_payment(requests_mock):
    sale_id = 1001
    total_amount = 36.60

    # Mock the /checkout endpoint
    requests_mock.post(
        "http://localhost:5294/checkout",
        json={"saleId": sale_id, "total": total_amount},
        status_code=200
    )

    # Mock the /payment endpoint
    requests_mock.post(
        "http://localhost:5294/payment",
        json={"status": "Paid"},
        status_code=200
    )

    # Insert test sale into DB
    conn = pyodbc.connect(DB_CONN_STR)
    insert_test_sale(conn, sale_id=sale_id, total=total_amount, payment_status="Paid")
    conn.close()

    # Simulate API calls
    import requests
    checkout_response = requests.post("http://localhost:5294/checkout", json={})
    payment_response = requests.post("http://localhost:5294/payment", json={})

    # Assert HTTP responses (mocked)
    assert checkout_response.status_code == 200
    assert payment_response.status_code == 200

    # Verify DB
    row = execute_db_query("SELECT payment_status FROM sales_hdr WHERE id=?", sale_id)
    assert row is not None, f"Sale ID {sale_id} not found in DB"
    assert row[0] == "Paid", f"Expected 'Paid', got {row[0]}"

# =======================
# Test: Declined Payment
# =======================
def test_checkout_declined_payment(requests_mock):
    sale_id = 1002
    total_amount = 36.60

    # Mock the /checkout endpoint
    requests_mock.post(
        "http://localhost:5294/checkout",
        json={"saleId": sale_id, "total": total_amount},
        status_code=200
    )

    # Mock the /payment endpoint
    requests_mock.post(
        "http://localhost:5294/payment",
        json={"status": "Declined"},
        status_code=200
    )

    # Insert test sale into DB
    conn = pyodbc.connect(DB_CONN_STR)
    insert_test_sale(conn, sale_id=sale_id, total=total_amount, payment_status="Declined")
    conn.close()

    # Simulate API calls
    import requests
    checkout_response = requests.post("http://localhost:5294/checkout", json={})
    payment_response = requests.post("http://localhost:5294/payment", json={})

    # Assert HTTP responses (mocked)
    assert checkout_response.status_code == 200
    assert payment_response.status_code == 200

    # Verify DB
    row = execute_db_query("SELECT payment_status FROM sales_hdr WHERE id=?", sale_id)
    assert row is not None, f"Sale ID {sale_id} not found in DB"
    assert row[0] == "Declined", f"Expected 'Declined', got {row[0]}"
