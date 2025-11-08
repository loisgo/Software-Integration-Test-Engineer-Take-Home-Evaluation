import requests
import pyodbc
import pytest
from datetime import datetime

BASE_URL = "http://localhost:5294"

# Database connection string configuration
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
        if params is not None:
            # Ensure params is a tuple
            if not isinstance(params, (tuple, list)):
                params = (params,)
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        row = cursor.fetchone()
        return row
    finally:
        cursor.close()
        conn.close()

# Insert a test sale row and return its auto-generated ID
def insert_test_sale(total, payment_status="Paid"):
    conn = pyodbc.connect(DB_CONN_STR)
    cursor = conn.cursor()
    try:
        # Prevent extra "rows affected" messages
        cursor.execute("SET NOCOUNT ON;")
        
        # Insert the sale
        cursor.execute(
            "INSERT INTO sales_hdr (sale_date, total, payment_status) VALUES (?, ?, ?)",
            (datetime.now(), total, payment_status)
        )
        
        # Immediately fetch the new ID
        cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT) AS new_id")
        new_id = cursor.fetchone()[0]
        
        # Commit transaction
        conn.commit()
        return new_id
    finally:
        cursor.close()
        conn.close()




# Test Scenario: Successful payment and database verification
def test_checkout_successful_payment(requests_mock):
    print("\n--- Running Test For Successful Payment ---")

    # Prepare Checkout Payload
    items = [
        {"Sku": "TEST 001", "Price": 11.20},
        {"Sku": "TEST 002", "Price": 12.20},
        {"Sku": "TEST 003", "Price": 13.20},
    ]
    expected_total = sum(item["Price"] for item in items)

    # Insert a test sale row in DB
    sale_id = insert_test_sale(total=expected_total, payment_status="Paid")

    # Mock /checkout response
    requests_mock.post(
        f"{BASE_URL}/checkout",
        json={"saleId": sale_id, "total": expected_total},
        status_code=200
    )

    # Mock /payment response
    requests_mock.post(
        f"{BASE_URL}/payment",
        json={"status": "Paid"},
        status_code=200
    )

    # POST /checkout (add sales)
    checkout_response = requests.post(f"{BASE_URL}/checkout", json={"Items": items})
    body = checkout_response.json()
    assert body["total"] == pytest.approx(expected_total)

    # POST /payment (successful payment)
    payment_payload = {"saleId": sale_id, "cardNumber": "00520205", "amount": body["total"]}
    payment_response = requests.post(f"{BASE_URL}/payment", json=payment_payload)
    payment_body = payment_response.json()
    assert payment_body["status"] == "Paid"

    # Verify Database Values
    row = execute_db_query("SELECT payment_status FROM sales_hdr WHERE id=?", sale_id)
    assert row is not None
    assert row[0] == "Paid"

    print(f"DB verification passed: payment_status = {row[0]}")


def test_checkout_declined_payment(requests_mock):
    print("\n--- Running Test For Declined Payment ---")

    # Prepare items
    items = [
        {"Sku": "TEST 001", "Price": 11.20},
        {"Sku": "TEST 002", "Price": 12.20},
        {"Sku": "TEST 003", "Price": 13.20},
    ]
    expected_total = sum(item["Price"] for item in items)

    # Insert a test sale row with Declined status
    sale_id = insert_test_sale(total=expected_total, payment_status="Declined")

    # Mock /checkout response
    requests_mock.post(
        f"{BASE_URL}/checkout",
        json={"saleId": sale_id, "total": expected_total},
        status_code=200
    )

    # Mock /payment response
    requests_mock.post(
        f"{BASE_URL}/payment",
        json={"status": "Declined"},
        status_code=200
    )

    # POST /checkout (add sales)
    checkout_response = requests.post(f"{BASE_URL}/checkout", json={"Items": items})
    body = checkout_response.json()
    assert body["total"] == pytest.approx(expected_total)

     # POST /payment (declined payment)
    payment_payload = {"saleId": sale_id, "cardNumber": "", "amount": body["total"]}    # "cardNumber": "12345oidwa"
    payment_response = requests.post(f"{BASE_URL}/payment", json=payment_payload)
    payment_body = payment_response.json()
    assert payment_body["status"] == "Declined"

    # Verify Database Values
    row = execute_db_query("SELECT payment_status FROM sales_hdr WHERE id=?", sale_id)
    assert row is not None
    assert row[0] == "Declined"

    print(f"DB verification passed: payment_status = {row[0]}")
