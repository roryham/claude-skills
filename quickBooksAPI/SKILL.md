---
name: quickbooks-api
description: QuickBooks Online API reference including authentication, endpoints, entity CRUD operations, query syntax, rate limits, error handling, and common gotchas. Use when writing code that interacts with QuickBooks Online, Intuit APIs, or QBO entities (invoices, customers, payments, deposits, sales receipts, etc.). Also triggered by mentions of "quickbooks", "QBO", "intuit API", or QuickBooks entity types.
---

# QuickBooks Online API Reference

## API Overview

- **API Version:** v3
- **Sandbox Base URL:** `https://sandbox-quickbooks.api.intuit.com`
- **Production Base URL:** `https://quickbooks.api.intuit.com`
- **All endpoints prefixed with:** `/v3/company/{realmId}/`
- **Minor Version:** Append `?minorversion=75` (latest) to all requests

### Required Headers

```
Accept: application/json
Content-Type: application/json
Authorization: Bearer {access_token}
```

## Authentication Summary

QuickBooks uses **OAuth 2.0** authorization code flow.

- **Authorization URL:** `https://appcenter.intuit.com/connect/oauth2`
- **Token URL:** `https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer`
- **Scope:** `com.intuit.quickbooks.accounting`
- **Access token lifetime:** 1 hour
- **Refresh token lifetime:** 100 days (must refresh before expiry or re-authorize)

See [references/oauth2.md](references/oauth2.md) for complete OAuth 2.0 implementation details.

## Endpoints Quick Reference

All endpoints use base: `/v3/company/{realmId}/`

### Transaction Entities

| Entity | Create (POST) | Read (GET) | Update (POST) | Delete (POST) | Query (GET) |
|--------|--------------|------------|---------------|---------------|-------------|
| Invoice | `/invoice` | `/invoice/{id}` | `/invoice` | `/invoice?operation=delete` | `/query?query=SELECT...` |
| SalesReceipt | `/salesreceipt` | `/salesreceipt/{id}` | `/salesreceipt` | `/salesreceipt?operation=delete` | `/query?query=SELECT...` |
| RefundReceipt | `/refundreceipt` | `/refundreceipt/{id}` | `/refundreceipt` | `/refundreceipt?operation=delete` | `/query?query=SELECT...` |
| Payment | `/payment` | `/payment/{id}` | `/payment` | `/payment?operation=delete` | `/query?query=SELECT...` |
| Deposit | `/deposit` | `/deposit/{id}` | `/deposit` | `/deposit?operation=delete` | `/query?query=SELECT...` |
| Bill | `/bill` | `/bill/{id}` | `/bill` | `/bill?operation=delete` | `/query?query=SELECT...` |
| BillPayment | `/billpayment` | `/billpayment/{id}` | `/billpayment` | `/billpayment?operation=delete` | `/query?query=SELECT...` |
| Purchase | `/purchase` | `/purchase/{id}` | `/purchase` | `/purchase?operation=delete` | `/query?query=SELECT...` |
| Estimate | `/estimate` | `/estimate/{id}` | `/estimate` | `/estimate?operation=delete` | `/query?query=SELECT...` |
| CreditMemo | `/creditmemo` | `/creditmemo/{id}` | `/creditmemo` | `/creditmemo?operation=delete` | `/query?query=SELECT...` |
| JournalEntry | `/journalentry` | `/journalentry/{id}` | `/journalentry` | `/journalentry?operation=delete` | `/query?query=SELECT...` |
| Transfer | `/transfer` | `/transfer/{id}` | `/transfer` | `/transfer?operation=delete` | `/query?query=SELECT...` |
| VendorCredit | `/vendorcredit` | `/vendorcredit/{id}` | `/vendorcredit` | `/vendorcredit?operation=delete` | `/query?query=SELECT...` |
| PurchaseOrder | `/purchaseorder` | `/purchaseorder/{id}` | `/purchaseorder` | `/purchaseorder?operation=delete` | `/query?query=SELECT...` |
| TimeActivity | `/timeactivity` | `/timeactivity/{id}` | `/timeactivity` | `/timeactivity?operation=delete` | `/query?query=SELECT...` |

**Void operations** (zero out instead of delete — preserves audit trail):

| Entity | Void (POST) |
|--------|------------|
| Invoice | `/invoice?operation=void` with `{"Id": "...", "SyncToken": "..."}` |
| SalesReceipt | `/salesreceipt?operation=void` with `{"Id": "...", "SyncToken": "...", "sparse": true}` |
| Payment | `/payment?operation=void` with `{"Id": "...", "SyncToken": "..."}` |

### Name-List Entities

| Entity | Create (POST) | Read (GET) | Update (POST) | Query (GET) |
|--------|--------------|------------|---------------|-------------|
| Customer | `/customer` | `/customer/{id}` | `/customer` | `/query?query=SELECT...` |
| Vendor | `/vendor` | `/vendor/{id}` | `/vendor` | `/query?query=SELECT...` |
| Employee | `/employee` | `/employee/{id}` | `/employee` | `/query?query=SELECT...` |
| Item | `/item` | `/item/{id}` | `/item` | `/query?query=SELECT...` |
| Account | `/account` | `/account/{id}` | `/account` | `/query?query=SELECT...` |
| Class | `/class` | `/class/{id}` | `/class` | `/query?query=SELECT...` |
| Department | `/department` | `/department/{id}` | `/department` | `/query?query=SELECT...` |
| TaxCode | — | `/taxcode/{id}` | — | `/query?query=SELECT...` |
| TaxRate | — | `/taxrate/{id}` | — | `/query?query=SELECT...` |
| TaxAgency | `/taxagency` | `/taxagency/{id}` | — | `/query?query=SELECT...` |
| PaymentMethod | `/paymentmethod` | `/paymentmethod/{id}` | `/paymentmethod` | `/query?query=SELECT...` |
| Term | `/term` | `/term/{id}` | `/term` | `/query?query=SELECT...` |

### Supporting Endpoints

| Endpoint | Method | Notes |
|----------|--------|-------|
| `/companyinfo/{realmId}` | GET | Company info — good for connection testing |
| `/preferences` | GET, POST | Company preferences (read/update) |
| `/attachable` | POST | Create/update/delete file attachments |
| `/attachable/{id}` | GET | Read attachment metadata |
| `/upload` | POST | Upload attachment files (multipart/form-data) |
| `/batch` | POST | Batch operations — up to 30 items per request |
| `/cdc` | GET | Change Data Capture — poll for changed entities |
| `/exchangerate` | GET | Currency exchange rates |
| `/taxservice/taxcode` | POST | Create new tax codes via TaxService |

### Reports

All reports: `GET /v3/company/{realmId}/reports/{ReportName}?minorversion=75`

Common query parameters: `start_date`, `end_date`, `accounting_method` (`Cash`/`Accrual`), `date_macro` (`This Month`, `Last Year`, etc.)

| Report | Endpoint | Description |
|--------|----------|-------------|
| ProfitAndLoss | `/reports/ProfitAndLoss` | Income and expense summary |
| ProfitAndLossDetail | `/reports/ProfitAndLossDetail` | Detailed P&L with transactions |
| BalanceSheet | `/reports/BalanceSheet` | Assets, liabilities, equity |
| CashFlow | `/reports/CashFlow` | Statement of cash flows |
| TrialBalance | `/reports/TrialBalance` | Trial balance report |
| GeneralLedger | `/reports/GeneralLedger` | All transactions by account |
| TransactionList | `/reports/TransactionList` | Filtered transaction listing |
| AccountList | `/reports/AccountList` | Chart of accounts listing |
| AgedReceivables | `/reports/AgedReceivables` | Summary A/R aging |
| AgedReceivableDetail | `/reports/AgedReceivableDetail` | Detailed A/R aging |
| AgedPayables | `/reports/AgedPayables` | Summary A/P aging |
| AgedPayableDetail | `/reports/AgedPayableDetail` | Detailed A/P aging |
| CustomerBalance | `/reports/CustomerBalance` | Customer balance summary |
| CustomerBalanceDetail | `/reports/CustomerBalanceDetail` | Customer balance detail |
| CustomerIncome | `/reports/CustomerIncome` | Income by customer |
| CustomerSales | `/reports/CustomerSales` | Sales by customer |
| VendorBalance | `/reports/VendorBalance` | Vendor balance summary |
| VendorBalanceDetail | `/reports/VendorBalanceDetail` | Vendor balance detail |
| VendorExpenses | `/reports/VendorExpenses` | Expenses by vendor |
| ItemSales | `/reports/ItemSales` | Sales by item/product |
| ClassSales | `/reports/ClassSales` | Sales by class |
| DepartmentSales | `/reports/DepartmentSales` | Sales by department |
| InventoryValuationSummary | `/reports/InventoryValuationSummary` | Inventory value summary |

See [references/entities.md](references/entities.md) for complete entity field details and CRUD patterns.

## Query Syntax Quick Reference

```sql
SELECT * FROM EntityName
  WHERE FieldName = 'value'
  AND DateField >= '2024-01-01'
  ORDERBY FieldName DESC
  STARTPOSITION 1
  MAXRESULTS 1000
```

- **Max results per query:** 1000
- **Default max results:** 100 (if MAXRESULTS not specified)
- **Operators:** `=`, `<`, `>`, `<=`, `>=`, `IN`, `LIKE`
- **Date format:** `'YYYY-MM-DD'`
- **String values:** Single-quoted, escape `'` as `\'`
- **LIKE wildcard:** `%` (e.g., `LIKE '%smith%'`)

See [references/queries.md](references/queries.md) for complete query language reference.

## Request Patterns

### Read (GET)

```
GET /v3/company/{realmId}/invoice/{invoiceId}?minorversion=75
Authorization: Bearer {access_token}
Accept: application/json
```

### Query (GET)

```
GET /v3/company/{realmId}/query?query=SELECT * FROM Invoice WHERE TxnDate >= '2024-01-01'&minorversion=75
Authorization: Bearer {access_token}
Accept: application/json
```

The query string must be URL-encoded.

### Create (POST)

```
POST /v3/company/{realmId}/invoice?minorversion=75
Authorization: Bearer {access_token}
Content-Type: application/json
Accept: application/json

{
  "Line": [...],
  "CustomerRef": {"value": "1"}
}
```

### Update (POST) — Full Update

QBO uses **sparse updates**. Send only the fields you want to change, plus `Id`, `SyncToken`, and `sparse: true`.

```
POST /v3/company/{realmId}/invoice?minorversion=75

{
  "Id": "123",
  "SyncToken": "0",
  "sparse": true,
  "DueDate": "2024-12-31"
}
```

### Delete (POST)

```
POST /v3/company/{realmId}/invoice?operation=delete

{
  "Id": "123",
  "SyncToken": "0"
}
```

**Note:** Name-list entities (Customer, Vendor, etc.) cannot be deleted — only deactivated by setting `Active: false`.

### Void (POST) — Zero Out Transaction

Voids preserve the transaction for audit trail instead of deleting it.

```
POST /v3/company/{realmId}/invoice?operation=void

{
  "Id": "123",
  "SyncToken": "0"
}
```

Supported on: Invoice, SalesReceipt, Payment.

### Batch (POST) — Multiple Operations

Execute up to 30 operations in a single HTTP request.

```
POST /v3/company/{realmId}/batch

{
  "BatchItemRequest": [
    {"bId": "1", "operation": "create", "Invoice": {...}},
    {"bId": "2", "operation": "query", "Query": "SELECT * FROM Customer WHERE Id = '1'"},
    {"bId": "3", "operation": "delete", "Invoice": {"Id": "99", "SyncToken": "0"}}
  ]
}
```

Each batch item needs a unique `bId`, an `operation` (`create`, `update`, `delete`, `query`), and the entity payload or query string.

### Change Data Capture (CDC)

Poll for entities changed since a given timestamp:

```
GET /v3/company/{realmId}/cdc?entities=Customer,Invoice,Payment&changedSince=2024-01-01T00:00:00-08:00
```

Returns all changed entities of the specified types since the timestamp. Useful for incremental sync.

## Rate Limits

| Limit | Value |
|-------|-------|
| Requests per minute (per realm) | 500 |
| Concurrent requests | 10 |
| Batch request size | 30 items |
| Query results per page | 1000 max |
| Payload size | 10 MB max |

**Throttled response:** HTTP 429 with `Retry-After` header. Implement exponential backoff.

**Practical safe rate:** ~400 requests/minute with 150ms delay between calls.

## Error Codes

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | — |
| 400 | Bad request | Check request body / query syntax |
| 401 | Unauthorized | Refresh access token |
| 403 | Forbidden | Check scopes / subscription |
| 404 | Not found | Verify entity ID and realmId |
| 429 | Too many requests | Retry after `Retry-After` seconds |
| 500 | Internal server error | Retry with backoff |
| 503 | Service unavailable | Retry with backoff |

### Common QBO Error Codes

| Error Code | Message | Cause |
|------------|---------|-------|
| 500 | Unsupported operation requested | Wrong HTTP method or endpoint |
| 610 | Object not found | Entity deleted or wrong ID |
| 2010 | Invalid reference ID | Referenced entity doesn't exist |
| 5010 | Stale object | SyncToken mismatch — re-read and retry |
| 6000 | Business validation error | Business rule violated |
| 6140 | Duplicate document number | DocNumber already exists |
| 6240 | Duplicate name | DisplayName already taken |

## Critical Gotchas

1. **Minor version matters:** Different minor versions return different fields and behavior. Always specify `?minorversion=75` explicitly. Test with the minor version you'll deploy with.

2. **Sparse updates require SyncToken:** Always read the current entity first to get the latest `SyncToken`. Stale SyncTokens return error 5010.

3. **Name-list entities can't be deleted:** Customer, Vendor, Employee, Item, Account — set `Active: false` instead of DELETE.

4. **Deleted entities are queryable:** Use `WHERE Active = true` to exclude soft-deleted name-list entities. Transaction deletes are permanent.

5. **Special characters in queries:** Single quotes in values must be escaped: `'O\'Brien'`. URL-encode the entire query string.

6. **100-day refresh token expiry:** Refresh tokens expire after 100 days of non-use. Implement proactive refresh (e.g., weekly) or users must re-authorize.

7. **Sandbox vs Production credentials:** Separate OAuth apps. Sandbox data is isolated. Never mix credentials.

8. **Entity references use `value` not `id`:** Reference fields like `CustomerRef` use `{"value": "123"}`, not `{"id": "123"}`.

9. **Line items require detail types:** Each `Line` object needs a `DetailType` field (e.g., `SalesItemLineDetail`, `AccountBasedExpenseLineDetail`) and corresponding detail object.

10. **Deposit LinkedTxn:** When creating deposits from payments/sales receipts, use `LinkedTxn` array with `TxnId`, `TxnType`, and `TxnLineId`.

11. **Query pagination is 1-based:** `STARTPOSITION 1` is the first record, not 0.

12. **CompanyInfo for connection testing:** `GET /v3/company/{realmId}/companyinfo/{realmId}` is the simplest way to verify credentials work.

13. **Multi-currency:** If multi-currency is enabled, transactions include `CurrencyRef`, `ExchangeRate`, and `HomeTotalAmt` fields. Exchange rates are auto-populated but can be overridden. Use `/exchangerate` endpoint to query current rates.

14. **Void vs Delete:** Voiding zeroes out a transaction but preserves it for audit trail. Deleting permanently removes it. Prefer void for invoices, sales receipts, and payments.

15. **CustomField:** Up to 3 custom fields per transaction entity. Must be defined in QBO UI first. Reference by `DefinitionId`, not name. Custom fields are strings only.

16. **Attachable files:** Use two-step process — first POST to `/upload` with multipart/form-data, then create/update an Attachable entity to link the file to a transaction.

17. **Batch operations:** Max 30 operations per batch. Each item is independent — a failure in one doesn't roll back others. Check each `BatchItemResponse` for individual status.

18. **CDC polling:** Change Data Capture returns all changes since a timestamp. Use for incremental sync. Max 30 days lookback. Always store the latest `time` from response for next poll.

19. **Duplicate transactions are common:** Customers may accidentally submit duplicate orders, creating multiple SalesReceipts, Invoices, or Deposits with the same amount, date, and customer. Never stop at the first match — always collect ALL matching records and flag duplicates for user review. Auto-processing a duplicate can result in double deposits or missed refunds. See [gas-patterns.md](references/gas-patterns.md) for duplicate-aware matching patterns.

## Reference Files

- **[Entity Reference](references/entities.md)** — All QBO entity types with fields, required/optional, and CRUD patterns
- **[OAuth 2.0 Reference](references/oauth2.md)** — Complete OAuth 2.0 flow, token management, and security
- **[Query Language Reference](references/queries.md)** — Full query syntax, operators, pagination, and entity-specific quirks
- **[Google Apps Script Patterns](references/gas-patterns.md)** — GAS-specific integration patterns from production code
