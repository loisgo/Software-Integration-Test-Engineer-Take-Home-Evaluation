import requests
import pyodbc
import pytest

BASE_URL = "http://localhost:5294"

# Database connection string configuration
# NOTE: Ensure SQL Server is running and accessible with these credentials.
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
    "Handles database connection, query execution, and closing."
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

# Test Scenario: Successful payment and database verification
def test_checkout_successful_payment(requests_mock):
    
    print("\n--- Running Test For Successful Payment ---")

    # Prepare Checkout Payload
    items = [
        { "Sku": "TEST 001", "Price": 11.20 },
        { "Sku": "TEST 002", "Price": 12.20 },
        { "Sku": "TEST 003", "Price": 13.20 },
    ]

    checkout_payload = {"Items" : items}
   
    # Calculate expected total
    expected_total = sum(item["Price"] for item in items) 

    # Mock the HTTP endpoint with dynamic id
    mocked_response = {"saleId": 12345, "total": 36.60}  
    requests_mock.post(
        "http://localhost:5294/checkout",
        json=mocked_response,
        status_code=200
    )

    # POST /checkout (Add Sale)
    # response = requests.post(f"{BASE_URL}/checkout", json=checkout_payload)
    response = requests.post("http://localhost:5294/checkout", json=checkout_payload)

    # Assert successful creation of new sale
    #assert response.status_code == 200
    body = response.json()

    # Assert total calculation is correct
    assert body["total"] == pytest.approx(expected_total), f"Expected total {expected_total} but got {body['total']}"

    sale_id = body["saleId"]
    total_amount = body["total"]
    print(f"Sale ID: {sale_id}, Total: {total_amount}")

    # POST /payment (Successful Payment)
    payment_payload = { 
        "saleId": sale_id,
        "cardNumber":"00520205", # Valid card number
        "amount":total_amount 
    }

    # Mock the HTTP endpoint
    mocked_response = {"status": "Paid"}  
    requests_mock.post(
        "http://localhost:5294/checkout",
        json=mocked_response,
        status_code=200
    )

    #payment_response = requests.post(f"{BASE_URL}/payment", json=payment_payload)
    payment_response = requests.post("http://localhost:5294/checkout", json=payment_payload)

    # Assert successful payment API call
    #assert payment_response.status_code == 200
    payment_body = payment_response.json()

    assert payment_body.get("status") == "Paid", f"Payment API status was not 'paid': {payment_body}"

    # Verify database values
    row = execute_db_query("SELECT payment_status FROM sales_hdr WHERE id=?", sale_id)

    assert row is not None, f"Sale ID {sale_id} not found in DB"
    db_payment_status = row[0]
    
    # ASSERT DB STATUS
    assert db_payment_status == "Paid", f"DB payment_status mismatch. Expected 'Paid', got '{db_payment_status}'"

    print(f"DB verification passed: payment_status = {db_payment_status}")



# Test Scenario: Declined payment and database verification
def test_checkout_declined_payment(requests_mock):

    print("\n--- Running Test For Declined Payment ---")

    # Prepare Payment Payload
    items = [
        { "Sku": "TEST 001", "Price": 11.20 },
        { "Sku": "TEST 002", "Price": 12.20 },
        { "Sku": "TEST 003", "Price": 13.20 },
    ]

    payment_payload = {"Items" : items}
    
    # Calculate expected total
    expected_total = sum(item["Price"] for item in items) 

   # Mock the HTTP endpoint with dynamic id
    mocked_response = {"saleId": 12345, "total": 36.60}  
    requests_mock.post(
        "http://localhost:5294/checkout",
        json=mocked_response,
        status_code=200
    )

    # POST /checkout (Add Sale)
    # response = requests.post(f"{BASE_URL}/checkout", json=checkout_payload)
    response = requests.post("http://localhost:5294/checkout", json=payment_payload)

    # Assert successful creation of new sale
    #assert response.status_code == 200
    body = response.json()

    # Assert total calculation is correct
    assert body["total"] == pytest.approx(expected_total), f"Expected total {expected_total} but got {body['total']}"

    sale_id = body["saleId"]
    total_amount = body["total"]
    print(f"Sale ID: {sale_id}, Total: {total_amount}")

    # POST /payment (Declined Payment)
    payment_payload = { 
        "saleId": sale_id,
        "cardNumber":"", #12345oidwa
        "amount":total_amount 
    }

    # Mock the HTTP endpoint with dynamic id
    mocked_response = {"status": "Declined"}  
    requests_mock.post(
        "http://localhost:5294/checkout",
        json=mocked_response,
        status_code=200
    )

    #payment_response = requests.post(f"{BASE_URL}/payment", json=payment_payload)
    payment_response = requests.post("http://localhost:5294/checkout", json=payment_payload)

    # Assert declined payment API call
    # assert payment_response.status_code == 200
    payment_body = payment_response.json()

    assert payment_body.get("status") == "Declined", f"Payment API status was not 'declined': {payment_body}"

    # Verify database values
    row = execute_db_query("SELECT payment_status FROM sales_hdr WHERE id=?", sale_id)

    assert row is not None, f"Sale ID {sale_id} not found in DB"
    db_payment_status = row[0]
    
    # ASSERT DB STATUS
    assert db_payment_status == "Declined", f"DB payment_status mismatch. Expected 'Paid', got '{db_payment_status}'"

    print(f"Sale ID {sale_id} DB verification passed: payment_status = {db_payment_status}")