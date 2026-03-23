# QuickBooks Online Query Language Reference

## Basic Syntax

```sql
SELECT * FROM EntityName
SELECT Id, DisplayName, Balance FROM EntityName
SELECT * FROM EntityName WHERE Condition
SELECT * FROM EntityName WHERE Condition ORDERBY Field [ASC|DESC]
SELECT * FROM EntityName STARTPOSITION N MAXRESULTS M
SELECT COUNT(*) FROM EntityName [WHERE Condition]
```

**Query endpoint:** `GET /v3/company/{realmId}/query?query={URL_ENCODED_QUERY}&minorversion=75`

## SELECT Clause

- `SELECT *` — Returns all fields
- `SELECT Field1, Field2` — Returns only specified fields
- `SELECT COUNT(*)` — Returns count only (in `totalCount` field)
- **No aliases, no expressions, no computed fields**

## WHERE Clause

### Comparison Operators

| Operator | Example | Notes |
|----------|---------|-------|
| `=` | `WHERE Id = '123'` | Exact match |
| `<` | `WHERE Balance < 100` | Less than |
| `>` | `WHERE Balance > 0` | Greater than |
| `<=` | `WHERE TxnDate <= '2024-12-31'` | Less than or equal |
| `>=` | `WHERE TxnDate >= '2024-01-01'` | Greater than or equal |
| `IN` | `WHERE Id IN ('1', '2', '3')` | Set membership |
| `LIKE` | `WHERE DisplayName LIKE '%smith%'` | Pattern match, `%` wildcard |

### Logical Operators

- `AND` — Combine conditions: `WHERE Balance > 0 AND Active = true`
- **No `OR` operator** — Use `IN` for multiple values on same field, or make separate queries
- **No `NOT` operator** — Use complementary conditions

### Value Types

| Type | Format | Example |
|------|--------|---------|
| String | Single-quoted | `'John Smith'` |
| Number | Unquoted | `100`, `99.50` |
| Boolean | Unquoted | `true`, `false` |
| Date | Single-quoted, YYYY-MM-DD | `'2024-01-15'` |
| DateTime | Single-quoted, ISO 8601 | `'2024-01-15T00:00:00-08:00'` |
| Enum | Single-quoted | `'Cash'` |

### Escaping Special Characters

- Single quote in value: `'O\'Brien'`
- The entire query string must be URL-encoded when sent via GET

## ORDERBY Clause

```sql
SELECT * FROM Customer ORDERBY DisplayName ASC
SELECT * FROM Invoice ORDERBY TxnDate DESC
```

- Default order: ASC (ascending)
- Only one ORDERBY field allowed per query
- Not all fields support ordering — typically Id, name fields, dates, and amounts

## Pagination

```sql
SELECT * FROM Customer STARTPOSITION 1 MAXRESULTS 100
SELECT * FROM Customer STARTPOSITION 101 MAXRESULTS 100
```

| Parameter | Default | Maximum | Notes |
|-----------|---------|---------|-------|
| STARTPOSITION | 1 | — | **1-based**, not 0-based |
| MAXRESULTS | 100 | 1000 | Per-query limit |

### Pagination Pattern

```javascript
var startPosition = 1;
var maxResults = 1000;
var allResults = [];

do {
  var query = "SELECT * FROM Customer STARTPOSITION " + startPosition + " MAXRESULTS " + maxResults;
  var response = queryQBO(query);
  var entities = response.QueryResponse.Customer || [];
  allResults = allResults.concat(entities);
  startPosition += maxResults;
} while (entities.length === maxResults);
```

### Paginated Invoice Query

Invoices often exceed 1000 results. Always paginate when querying by date range:

```javascript
function getAllInvoices(startDate, endDate) {
  var startPosition = 1;
  var maxResults = 1000;
  var allInvoices = [];

  do {
    var query = "SELECT * FROM Invoice"
      + " WHERE TxnDate >= '" + startDate + "'"
      + " AND TxnDate <= '" + endDate + "'"
      + " STARTPOSITION " + startPosition
      + " MAXRESULTS " + maxResults;
    var response = queryQBO(query);
    var invoices = response.QueryResponse.Invoice || [];
    allInvoices = allInvoices.concat(invoices);
    startPosition += maxResults;
  } while (invoices.length === maxResults);

  return allInvoices;
}
```

### Paginated SalesReceipt Query

SalesReceipts follow the same pattern — note the response key is `SalesReceipt` (not `SalesReceipts`):

```javascript
function getAllSalesReceipts(startDate, endDate) {
  var startPosition = 1;
  var maxResults = 1000;
  var allReceipts = [];

  do {
    var query = "SELECT * FROM SalesReceipt"
      + " WHERE TxnDate >= '" + startDate + "'"
      + " AND TxnDate <= '" + endDate + "'"
      + " STARTPOSITION " + startPosition
      + " MAXRESULTS " + maxResults;
    var response = queryQBO(query);
    var receipts = response.QueryResponse.SalesReceipt || [];
    allReceipts = allReceipts.concat(receipts);
    startPosition += maxResults;
  } while (receipts.length === maxResults);

  return allReceipts;
}
```

**Critical:** The response array key must exactly match the entity name used in the query — `Invoice`, `SalesReceipt`, `Customer`, etc. A mismatch (e.g., `SalesReceipts` instead of `SalesReceipt`) silently returns an empty array and breaks pagination.

## Query Response Format

```json
{
  "QueryResponse": {
    "Customer": [
      { "Id": "1", "DisplayName": "John Smith", ... },
      { "Id": "2", "DisplayName": "Jane Doe", ... }
    ],
    "startPosition": 1,
    "maxResults": 2,
    "totalCount": 2
  },
  "time": "2024-01-15T10:30:00.000-08:00"
}
```

- Entity array key matches the entity name (e.g., `Customer`, `Invoice`, `Deposit`)
- `totalCount` only present with `SELECT COUNT(*)` or on last page
- Empty result: `QueryResponse` contains only `startPosition` and `maxResults` (no entity array)

## Common Query Examples

### Customers

```sql
-- All active customers
SELECT * FROM Customer WHERE Active = true

-- Customer by display name
SELECT * FROM Customer WHERE DisplayName = 'John Smith'

-- Customer search by partial name
SELECT * FROM Customer WHERE DisplayName LIKE '%smith%'

-- Customers with email
SELECT Id, DisplayName, PrimaryEmailAddr FROM Customer

-- Customer count
SELECT COUNT(*) FROM Customer
```

### Invoices

```sql
-- Invoices for a date range
SELECT * FROM Invoice WHERE TxnDate >= '2024-01-01' AND TxnDate <= '2024-12-31'

-- Unpaid invoices
SELECT * FROM Invoice WHERE Balance > 0

-- Invoices for a specific customer
SELECT * FROM Invoice WHERE CustomerRef = '123'

-- Overdue invoices (past due date)
SELECT * FROM Invoice WHERE DueDate < '2024-03-01' AND Balance > 0
```

### Sales Receipts

```sql
-- Sales receipts for a date range
SELECT * FROM SalesReceipt WHERE TxnDate >= '2024-01-01' AND TxnDate <= '2024-01-31'

-- Sales receipts by customer
SELECT * FROM SalesReceipt WHERE CustomerRef = '42'
```

### Deposits

```sql
-- Deposits on a specific date
SELECT * FROM Deposit WHERE TxnDate = '2024-01-15'

-- Deposits in a date range
SELECT * FROM Deposit WHERE TxnDate >= '2024-01-01' AND TxnDate <= '2024-01-31'
```

### Payments

```sql
-- Payments for a customer
SELECT * FROM Payment WHERE CustomerRef = '123'

-- Payments in a date range
SELECT * FROM Payment WHERE TxnDate >= '2024-01-01' AND TxnDate <= '2024-12-31'
```

### Accounts

```sql
-- All bank accounts
SELECT * FROM Account WHERE AccountType = 'Bank' AND Active = true

-- Account by name
SELECT * FROM Account WHERE Name = 'Checking'

-- All expense accounts
SELECT * FROM Account WHERE AccountType = 'Expense'
```

### Items

```sql
-- All active items
SELECT * FROM Item WHERE Active = true

-- Items by type
SELECT * FROM Item WHERE Type = 'Service'

-- Item by name
SELECT * FROM Item WHERE Name = 'Consulting'
```

### Vendors

```sql
-- Active vendors
SELECT * FROM Vendor WHERE Active = true

-- Vendor by name
SELECT * FROM Vendor WHERE DisplayName LIKE '%supply%'
```

### Bills

```sql
-- Unpaid bills
SELECT * FROM Bill WHERE Balance > 0

-- Bills for a specific vendor
SELECT * FROM Bill WHERE VendorRef = '42'

-- Bills due soon
SELECT * FROM Bill WHERE DueDate <= '2024-03-01' AND Balance > 0
```

### Estimates

```sql
-- Open estimates
SELECT * FROM Estimate WHERE TxnStatus = 'Pending'

-- Estimates for a customer
SELECT * FROM Estimate WHERE CustomerRef = '123'
```

### Credit Memos

```sql
-- Credit memos with remaining credit
SELECT * FROM CreditMemo WHERE RemainingCredit > 0

-- Credit memos by customer
SELECT * FROM CreditMemo WHERE CustomerRef = '123'
```

### Journal Entries

```sql
-- Journal entries in a date range
SELECT * FROM JournalEntry WHERE TxnDate >= '2024-01-01' AND TxnDate <= '2024-12-31'
```

### Time Activities

```sql
-- Billable time activities
SELECT * FROM TimeActivity WHERE BillableStatus = 'Billable'

-- Time activities for an employee
SELECT * FROM TimeActivity WHERE EmployeeRef = '55'

-- Time activities in a date range
SELECT * FROM TimeActivity WHERE TxnDate >= '2024-01-01' AND TxnDate <= '2024-01-31'
```

### Attachables

```sql
-- All attachables
SELECT * FROM Attachable

-- Attachables for a specific note content
SELECT * FROM Attachable WHERE Note LIKE '%receipt%'
```

### Tax Codes and Rates

```sql
-- All active tax codes
SELECT * FROM TaxCode WHERE Active = true

-- All tax rates
SELECT * FROM TaxRate
```

### Classes and Departments

```sql
-- All active classes
SELECT * FROM Class WHERE Active = true

-- All departments
SELECT * FROM Department WHERE Active = true
```

### Terms and Payment Methods

```sql
-- All active terms
SELECT * FROM Term WHERE Active = true

-- All payment methods
SELECT * FROM PaymentMethod WHERE Active = true
```

### Transfers

```sql
-- Transfers in a date range
SELECT * FROM Transfer WHERE TxnDate >= '2024-01-01' AND TxnDate <= '2024-12-31'
```

### Purchase Orders

```sql
-- Open purchase orders
SELECT * FROM PurchaseOrder WHERE POStatus = 'Open'

-- Purchase orders for a vendor
SELECT * FROM PurchaseOrder WHERE VendorRef = '42'
```

### Changed Entities (CDC Alternative)

```sql
-- Entities modified since a date
SELECT * FROM Customer WHERE MetaData.LastUpdatedTime >= '2024-01-01T00:00:00-08:00'
SELECT * FROM Invoice WHERE MetaData.LastUpdatedTime >= '2024-01-01T00:00:00-08:00'
```

**Note:** For efficient change detection across multiple entity types, use the CDC endpoint instead (see entities reference).

## Entity-Specific Query Quirks

### Customer / Vendor / Employee
- Use `DisplayName` for searching, not `Name` (Name is not directly queryable on all entities)
- `GivenName` and `FamilyName` are separate fields — `DisplayName` is the combined display value
- `PrimaryEmailAddr` is an object — cannot directly query by email address

### Invoice
- `Balance` field represents remaining unpaid amount
- `TotalAmt` is the full invoice amount
- Query by `DocNumber` to find by invoice number: `WHERE DocNumber = 'INV-1001'`

### Account
- `AccountType` values: `Bank`, `Accounts Receivable`, `Other Current Asset`, `Fixed Asset`, `Other Asset`, `Accounts Payable`, `Credit Card`, `Other Current Liability`, `Long Term Liability`, `Equity`, `Income`, `Cost of Goods Sold`, `Expense`, `Other Income`, `Other Expense`
- `AccountSubType` provides finer categorization

### Item
- `Type` values: `Inventory`, `Service`, `NonInventory`, `Group`, `Category`
- Query `Type = 'Service'` or `Type = 'Inventory'` to filter

### Deposit
- Cannot query by linked transaction — must read the deposit and check `Line[].LinkedTxn`
- Query by date and then filter client-side for specific linked transactions

### TaxCode / TaxRate
- Read-only — can query but not create or update via API (use TaxService endpoint to create)
- `SELECT * FROM TaxCode WHERE Active = true`

### TimeActivity
- Query by `BillableStatus`: `'Billable'`, `'NotBillable'`, `'HasBeenBilled'`
- Can filter by `EmployeeRef` or `VendorRef` depending on `NameOf`
- Date filtering uses `TxnDate`, not `StartTime`/`EndTime`

### Attachable
- Can query by `Note` field using LIKE
- Cannot query by linked entity — must read individual attachables
- File metadata (FileName, ContentType) is not queryable

### PurchaseOrder
- `POStatus` values: `'Open'`, `'Closed'`
- Can filter by `VendorRef`

### Estimate
- `TxnStatus` values: `'Pending'`, `'Accepted'`, `'Closed'`, `'Rejected'`
- Useful for filtering actionable quotes

### Bill / BillPayment
- Bills: filter by `VendorRef`, `DueDate`, `Balance`
- BillPayments: filter by `VendorRef`, `TxnDate`

### CreditMemo
- `RemainingCredit` tracks unused credit amount
- Filter `RemainingCredit > 0` to find applicable credits

### Queryable Entity List

All entities that support the query endpoint:

| Entity | Key Queryable Fields |
|--------|---------------------|
| Account | Name, AccountType, AccountSubType, Active, Classification |
| Attachable | Note |
| Bill | VendorRef, TxnDate, DueDate, Balance, DocNumber |
| BillPayment | VendorRef, TxnDate |
| Class | Name, Active |
| CreditMemo | CustomerRef, TxnDate, RemainingCredit, DocNumber |
| Customer | DisplayName, GivenName, FamilyName, CompanyName, Active, Balance |
| Department | Name, Active |
| Deposit | TxnDate |
| Employee | DisplayName, GivenName, FamilyName, Active |
| Estimate | CustomerRef, TxnDate, TxnStatus, DocNumber |
| Invoice | CustomerRef, TxnDate, DueDate, Balance, DocNumber |
| Item | Name, Type, Active |
| JournalEntry | TxnDate, DocNumber |
| Payment | CustomerRef, TxnDate |
| PaymentMethod | Name, Active |
| Purchase | AccountRef, TxnDate, PaymentType |
| PurchaseOrder | VendorRef, TxnDate, POStatus, DocNumber |
| RefundReceipt | CustomerRef, TxnDate |
| SalesReceipt | CustomerRef, TxnDate, DocNumber |
| TaxCode | Name, Active |
| TaxRate | Name, Active |
| Term | Name, Active |
| TimeActivity | EmployeeRef, VendorRef, TxnDate, BillableStatus |
| Transfer | TxnDate |
| Vendor | DisplayName, CompanyName, Active, Balance |
| VendorCredit | VendorRef, TxnDate |

## URL Encoding

The query string must be URL-encoded when sent as a GET parameter:

```
Original: SELECT * FROM Customer WHERE DisplayName = 'O'Brien'
Escaped:  SELECT * FROM Customer WHERE DisplayName = 'O\'Brien'
Encoded:  SELECT%20*%20FROM%20Customer%20WHERE%20DisplayName%20%3D%20'O%5C'Brien'
```

In Google Apps Script, use `encodeURIComponent()`:
```javascript
var query = "SELECT * FROM Customer WHERE DisplayName LIKE '%smith%'";
var url = baseUrl + "/query?query=" + encodeURIComponent(query) + "&minorversion=75";
```

## Limitations

- **No JOINs** — Each query targets one entity type
- **No OR operator** — Use `IN` or multiple queries
- **No subqueries** — Use client-side filtering
- **No GROUP BY or aggregate functions** — Only `COUNT(*)`
- **Max 1000 results per query** — Paginate for more
- **No nested field queries** — Cannot query `Line.Amount` or similar nested fields (except `MetaData.LastUpdatedTime`)
- **Case-sensitive values** — `WHERE DisplayName = 'john'` won't match `John`
- **LIKE is case-insensitive** — `WHERE DisplayName LIKE '%john%'` matches `John`, `JOHN`, etc.
