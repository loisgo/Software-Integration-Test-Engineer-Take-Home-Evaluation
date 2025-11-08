# Software Integration Test Engineer Take-Home Evaluation

## Overview

This project contains automated integration test coverage for a Sales Checkout + Payment backend system.

The purpose of these tests is to validate full request → storage → payment processing behavior using SQL Server as the backing database.

The goal of this test pack is to ensure:

- /checkout API calculates totals correctly and creates sales records
- /payment API applies payment logic and updates database status
- SQL Server data integrity (sales_hdr + sales_lin) remains correct
- Tests can run locally + inside CI repeatably without environment drift
- External gateways (payment) are mocked to isolate system behavior

---

## Technology and Tools

| Area                 | Tools / Tech                  |
| -------------------- | ----------------------------- |
| Language             | Python                        |
| Test Framework       | Pytest                        |
| DB                   | Microsoft SQL Server          |
| Driver               | ODBC Driver 18 for SQL Server |
| Payment Gateway Mock | Mockoon                       |
| CI                   | GitHub Actions                |

---

## Test Plan Overview

### Checkout API (`POST /checkout`)

**Happy Path**

1. **New sale on empty DB**

   - Database has no existing sales
   - Expect: New sale inserted into `sales_hdr`, line items inserted into `sales_lin`
   - Validate: Response returns valid `saleId` and total equals sum of item prices
   - Validate: `line_no` increments sequentially starting at 1

2. **New sale with existing DB data**
   - Database contains historical sales
   - Expect: New sale inserted correctly, no existing rows modified
   - Validate: `saleId` increments correctly, total is accurate
   - Validate: `line_no` increments sequentially starting at 1

**Negative Path**

1. **Missing required fields (sku or price)**

   - Partial invalid item in request
   - Expect: API returns 4xx error, database unchanged

2. **Invalid JSON format**

   - Malformed request body
   - Expect: API returns 400 error, database unchanged

3. **Empty body**
   - Empty JSON object or array
   - Expect: API returns 400 error, database unchanged

---

### Payment API (`POST /payment`)

**Happy Path**

1. **Valid payment**
   - `saleId` exists, valid card, correct amount
   - Expect: API returns 200, `payment_status` updated to `Paid`
   - Validate: Only the corresponding sale row is updated

**Negative Path**

1. **Non-existing saleId**

   - `saleId` not present in DB
   - Expect: API returns error, DB unchanged

2. **Invalid payment input**

   - Invalid or missing card number, amount, or empty JSON
   - Expect: Validation error (4xx), DB unchanged

3. **Valid saleId but declined payment**

   - Payment gateway returns `Declined`
   - Expect: API returns 200 (or gateway-appropriate error)
   - Validate: DB updates `payment_status` to `Declined`

4. **Amount mismatch**
   - Payment amount != checkout total
   - Expect: 4xx error (if validation enforced) or system-defined behavior
   - Validate: DB unchanged

---

## Setup Instructions

### Local Environment

1. Clone the repository:

```bash
git clone <repo_url>
cd Software-Integration-Test-Engineer-Take-Home-Evaluation
```

2. Create a virtual environment and activate it:

```bash
python3 -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

3. Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. Ensure SQL Server is running locally on port 1433 with a database MySalesDB.

Recommended (Docker)

```bash
docker run -e "ACCEPT_EULA=Y" \
 -e "SA_PASSWORD={{password}}" \
 -p 1433:1433 \
 --name sql-local \
 -d mcr.microsoft.com/mssql/server:2022-latest
```

Create database:

```bash
docker exec -it sql-local /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P {{password}} -Q "CREATE DATABASE MySalesDB"
```

5. Mock Payment Gateway (Mockoon)

- Mockoon simulates external gateway responses so tests don’t depend on real processors.
- Install Mockoon: https://mockoon.com/
- Import provided mock definition JSON (mockoon/env/payment-gateway.json)
- Start mock API server locally
- Point your /payment route in test config to this mock endpoint during testing

6. Run tests locally with mocked Payment API (e.g., using Mockoon):

```bash
pytest --junitxml=reports/junit.xml \
       --cov=./ \
       --cov-report xml:reports/coverage.xml \
       --cov-fail-under=70 \
       --cov-report term-missing
```

---

### CI Pipeline (GitHub Actions)

- Workflow triggers on push, pull request, or manual dispatch
- Steps include:

  1. Checkout code
  2. Set up Python 3.14
  3. Install dependencies
  4. Start SQL Server container (`mcr.microsoft.com/mssql/server:2022-latest`)
  5. Install SQL Server ODBC driver and tools
  6. Wait for SQL Server to be ready
  7. Create database `MySalesDB` and schema (`schema.sql`)
  8. Run pytest with coverage
  9. Upload reports as artifacts

- Secrets:
  - `SA_PASSWORD` — Strong password for SQL Server container

**Note:** External HTTP services (payment gateway) are mocked in CI to ensure deterministic tests.

---

## Test Execution Notes

- Use `requests_mock` to mock `/checkout` and `/payment` endpoints in CI
- Insert expected rows manually into `sales_hdr` for database assertions
- Coverage reports highlight untested lines
