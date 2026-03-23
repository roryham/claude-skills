# QuickBooks Online Entity Reference

## Transaction Entities

### Invoice

**Description:** A sales form representing an amount owed by a customer.

**Endpoint:** `/v3/company/{realmId}/invoice`

**Required fields for create:**
- `Line[]` — At least one line item
  - `Amount` — Line amount
  - `DetailType` — `"SalesItemLineDetail"`
  - `SalesItemLineDetail.ItemRef.value` — Item ID
- `CustomerRef.value` — Customer ID

**Key optional fields:**
- `DocNumber` — Invoice number (auto-generated if omitted)
- `TxnDate` — Transaction date (default: today)
- `DueDate` — Payment due date
- `BillEmail.Address` — Email for sending
- `PrivateNote` — Internal memo
- `CustomerMemo.value` — Memo visible to customer
- `SalesTermRef.value` — Payment terms ID
- `DepartmentRef.value` — Department/location ID
- `ClassRef.value` — Class ID (per-line or per-transaction)
- `TxnTaxDetail` — Tax information
- `ShipAddr`, `BillAddr` — Shipping/billing addresses
- `AllowIPNPayment` — Allow Intuit Payment Network
- `AllowOnlinePayment` — Allow online payment
- `AllowOnlineCreditCardPayment` — Allow credit card online
- `AllowOnlineACHPayment` — Allow ACH/bank transfer online
- `Deposit` — Deposit amount collected
- `PrintStatus` — `"NotSet"`, `"NeedToPrint"`, `"PrintComplete"`
- `EmailStatus` — `"NotSet"`, `"NeedToSend"`, `"EmailSent"`
- `ApplyTaxAfterDiscount` — Tax calculation order
- `CustomField[]` — Up to 3 custom fields (define in QBO UI first)
- `CurrencyRef` — Multi-currency: currency reference
- `ExchangeRate` — Multi-currency: exchange rate override

**Read-only fields:** `Id`, `SyncToken`, `Balance`, `TotalAmt`, `HomeTotalAmt`, `MetaData`, `LinkedTxn`

**Void operation:** `POST /invoice?operation=void` with `{"Id": "...", "SyncToken": "..."}`

---

### SalesReceipt

**Description:** A sales form for immediate payment (no accounts receivable).

**Endpoint:** `/v3/company/{realmId}/salesreceipt`

**Required fields for create:**
- `Line[]` — At least one line item
  - `Amount`, `DetailType: "SalesItemLineDetail"`, `SalesItemLineDetail.ItemRef.value`
- `CustomerRef.value` — Customer ID

**Key optional fields:**
- `DocNumber` — Receipt number
- `TxnDate` — Transaction date
- `DepositToAccountRef.value` — Bank account ID (default: Undeposited Funds)
- `PaymentMethodRef.value` — Payment method ID
- `PaymentRefNum` — Check/reference number
- `PrivateNote`, `CustomerMemo.value`
- `BillEmail.Address`
- `DepartmentRef.value`, `ClassRef.value`
- `PrintStatus` — `"NotSet"`, `"NeedToPrint"`, `"PrintComplete"`
- `EmailStatus` — `"NotSet"`, `"NeedToSend"`, `"EmailSent"`
- `ApplyTaxAfterDiscount` — Tax calculation order
- `CustomField[]` — Up to 3 custom fields
- `CurrencyRef`, `ExchangeRate` — Multi-currency support

**Read-only fields:** `Id`, `SyncToken`, `TotalAmt`, `HomeTotalAmt`, `Balance`, `MetaData`

**Void operation:** `POST /salesreceipt?operation=void` with `{"Id": "...", "SyncToken": "...", "sparse": true}`

**Notes:** When `DepositToAccountRef` is Undeposited Funds, the receipt can be linked to a Deposit entity later.

---

### RefundReceipt

**Description:** A refund given to a customer (negative sales receipt).

**Endpoint:** `/v3/company/{realmId}/refundreceipt`

**Required fields for create:**
- `Line[]` — At least one line item
- `CustomerRef.value` — Customer ID
- `DepositToAccountRef.value` — Account to refund from

**Key optional fields:**
- `DocNumber`, `TxnDate`, `PrivateNote`
- `PaymentMethodRef.value`, `PaymentRefNum`
- `CheckPayment` — For check refunds
- `DepartmentRef.value`, `ClassRef.value`
- `PrintStatus`, `EmailStatus`
- `ApplyTaxAfterDiscount`
- `CustomField[]` — Up to 3 custom fields
- `CurrencyRef`, `ExchangeRate` — Multi-currency support

**Read-only fields:** `Id`, `SyncToken`, `TotalAmt`, `HomeTotalAmt`, `Balance`, `MetaData`

---

### Payment

**Description:** Payment received from a customer against an outstanding invoice.

**Endpoint:** `/v3/company/{realmId}/payment`

**Required fields for create:**
- `TotalAmt` — Payment amount
- `CustomerRef.value` — Customer ID

**Key optional fields:**
- `Line[]` — Links to invoices being paid
  - `Amount` — Amount applied to this invoice
  - `LinkedTxn[].TxnId` — Invoice ID
  - `LinkedTxn[].TxnType` — `"Invoice"`
- `DepositToAccountRef.value` — Bank account (default: Undeposited Funds)
- `PaymentMethodRef.value` — Payment method ID
- `PaymentRefNum` — Check/reference number
- `TxnDate` — Payment date
- `PrivateNote`
- `ProcessPayment` — `true` to process via Intuit Payments
- `CurrencyRef`, `ExchangeRate` — Multi-currency support

**Read-only fields:** `Id`, `SyncToken`, `UnappliedAmt`, `MetaData`

**Void operation:** `POST /payment?operation=void` with `{"Id": "...", "SyncToken": "..."}`

**Notes:** If no `Line` items specified, payment goes to Undeposited Funds without applying to any invoice.

---

### Deposit

**Description:** A bank deposit grouping payments, sales receipts, or other funds.

**Endpoint:** `/v3/company/{realmId}/deposit`

**Required fields for create:**
- `DepositToAccountRef.value` — Bank account ID
- `Line[]` — At least one line item

**Line item types:**

1. **Linked transactions** (payments/sales receipts from Undeposited Funds):
```json
{
  "Amount": 100.00,
  "LinkedTxn": [{
    "TxnId": "123",
    "TxnType": "SalesReceipt",
    "TxnLineId": "0"
  }]
}
```

2. **Direct deposit lines** (cash/other income):
```json
{
  "Amount": 50.00,
  "DetailType": "DepositLineDetail",
  "DepositLineDetail": {
    "AccountRef": {"value": "1", "name": "Sales"},
    "Entity": {
      "value": "456",
      "type": "Customer"
    }
  }
}
```

**Key optional fields:**
- `TxnDate` — Deposit date
- `PrivateNote` — Memo
- `CashBack` — Cash back from deposit
- `DepartmentRef.value`
- `CurrencyRef`, `ExchangeRate` — Multi-currency support

**Read-only fields:** `Id`, `SyncToken`, `TotalAmt`, `MetaData`

**Notes:**
- `TxnType` for LinkedTxn: `"Payment"`, `"SalesReceipt"`, `"RefundReceipt"`, `"JournalEntry"`, `"CashPurchase"`
- `TxnLineId` is typically `"0"` for the first line of the linked transaction
- Linked transactions must be in Undeposited Funds to be deposited

---

### Bill

**Description:** An amount owed to a vendor for goods or services.

**Endpoint:** `/v3/company/{realmId}/bill`

**Required fields for create:**
- `VendorRef.value` — Vendor ID
- `Line[]` — At least one line item
  - For item-based: `DetailType: "ItemBasedExpenseLineDetail"`, `ItemBasedExpenseLineDetail.ItemRef.value`
  - For account-based: `DetailType: "AccountBasedExpenseLineDetail"`, `AccountBasedExpenseLineDetail.AccountRef.value`

**Key optional fields:**
- `DocNumber`, `TxnDate`, `DueDate`
- `APAccountRef.value` — Accounts payable account
- `SalesTermRef.value` — Payment terms
- `PrivateNote`
- `DepartmentRef.value`, `ClassRef.value`

**Read-only fields:** `Id`, `SyncToken`, `Balance`, `TotalAmt`, `MetaData`

---

### BillPayment

**Description:** Payment made to a vendor for an outstanding bill.

**Endpoint:** `/v3/company/{realmId}/billpayment`

**Required fields for create:**
- `VendorRef.value` — Vendor ID
- `TotalAmt` — Payment amount
- `PayType` — `"Check"` or `"CreditCard"`
- `Line[]` — Links to bills being paid
  - `Amount` — Amount applied
  - `LinkedTxn[].TxnId` — Bill ID
  - `LinkedTxn[].TxnType` — `"Bill"`
- Payment detail (one of):
  - `CheckPayment.BankAccountRef.value` — For check payments
  - `CreditCardPayment.CCAccountRef.value` — For credit card payments

**Read-only fields:** `Id`, `SyncToken`, `MetaData`

---

### Purchase

**Description:** An expense transaction (check, cash, credit card charge).

**Endpoint:** `/v3/company/{realmId}/purchase`

**Required fields for create:**
- `PaymentType` — `"Cash"`, `"Check"`, or `"CreditCard"`
- `AccountRef.value` — Bank/CC account ID
- `Line[]` — At least one line item
  - `DetailType: "AccountBasedExpenseLineDetail"` or `"ItemBasedExpenseLineDetail"`

**Key optional fields:**
- `EntityRef` — Vendor/customer reference
- `TxnDate`, `DocNumber`, `PrivateNote`
- `DepartmentRef.value`, `ClassRef.value`
- `Credit` — `true` if this is a credit/refund transaction
- `CustomField[]` — Up to 3 custom fields
- `CurrencyRef`, `ExchangeRate` — Multi-currency support

**Read-only fields:** `Id`, `SyncToken`, `TotalAmt`, `MetaData`

---

### PurchaseOrder

**Description:** A request to purchase goods/services from a vendor.

**Endpoint:** `/v3/company/{realmId}/purchaseorder`

**Required fields for create:**
- `VendorRef.value` — Vendor ID
- `Line[]` — At least one line item
  - `DetailType: "ItemBasedExpenseLineDetail"`, `ItemBasedExpenseLineDetail.ItemRef.value`
  - `Amount`

**Key optional fields:**
- `APAccountRef.value`, `DocNumber`, `TxnDate`
- `ShipTo`, `ShipAddr`, `VendorAddr`
- `DepartmentRef.value`, `ClassRef.value`

**Read-only fields:** `Id`, `SyncToken`, `TotalAmt`, `MetaData`, `POStatus`

---

### Estimate

**Description:** A quote or proposal for a customer.

**Endpoint:** `/v3/company/{realmId}/estimate`

**Required fields for create:**
- `CustomerRef.value` — Customer ID
- `Line[]` — At least one line item

**Key optional fields:**
- `DocNumber`, `TxnDate`, `ExpirationDate`
- `BillEmail.Address`
- `TxnStatus` — `"Pending"`, `"Accepted"`, `"Closed"`, `"Rejected"`
- `PrivateNote`, `CustomerMemo.value`

**Read-only fields:** `Id`, `SyncToken`, `TotalAmt`, `MetaData`

---

### CreditMemo

**Description:** A credit issued to a customer (reduces amount owed).

**Endpoint:** `/v3/company/{realmId}/creditmemo`

**Required fields for create:**
- `CustomerRef.value` — Customer ID
- `Line[]` — At least one line item

**Key optional fields:**
- `DocNumber`, `TxnDate`, `PrivateNote`
- `BillEmail.Address`
- `DepartmentRef.value`, `ClassRef.value`

**Read-only fields:** `Id`, `SyncToken`, `TotalAmt`, `RemainingCredit`, `MetaData`

---

### JournalEntry

**Description:** Manual journal entry with debits and credits.

**Endpoint:** `/v3/company/{realmId}/journalentry`

**Required fields for create:**
- `Line[]` — At least two lines (debits must equal credits)
  - `DetailType: "JournalEntryLineDetail"`
  - `JournalEntryLineDetail.PostingType` — `"Debit"` or `"Credit"`
  - `JournalEntryLineDetail.AccountRef.value` — Account ID
  - `Amount`

**Key optional fields:**
- `DocNumber`, `TxnDate`, `PrivateNote`
- `JournalEntryLineDetail.Entity` — Customer/vendor reference per line
- `JournalEntryLineDetail.ClassRef.value`
- `JournalEntryLineDetail.DepartmentRef.value`

**Read-only fields:** `Id`, `SyncToken`, `TotalAmt`, `MetaData`

---

### Transfer

**Description:** Fund transfer between two accounts.

**Endpoint:** `/v3/company/{realmId}/transfer`

**Required fields for create:**
- `FromAccountRef.value` — Source account ID
- `ToAccountRef.value` — Destination account ID
- `Amount` — Transfer amount

**Key optional fields:**
- `TxnDate`, `PrivateNote`

**Read-only fields:** `Id`, `SyncToken`, `MetaData`

---

### VendorCredit

**Description:** Credit from a vendor that reduces the amount owed.

**Endpoint:** `/v3/company/{realmId}/vendorcredit`

**Required fields for create:**
- `VendorRef.value` — Vendor ID
- `Line[]` — At least one line item

**Key optional fields:**
- `DocNumber`, `TxnDate`, `PrivateNote`
- `APAccountRef.value`
- `DepartmentRef.value`, `ClassRef.value`

**Read-only fields:** `Id`, `SyncToken`, `TotalAmt`, `Balance`, `MetaData`

---

### TimeActivity

**Description:** Time tracked by an employee or vendor for billing or payroll purposes.

**Endpoint:** `/v3/company/{realmId}/timeactivity`

**Required fields for create:**
- `NameOf` — `"Employee"` or `"Vendor"` (who performed the work)
- `EmployeeRef.value` or `VendorRef.value` — Corresponding to `NameOf`
- `StartTime` — Start time (ISO 8601 datetime)
- `EndTime` — End time (ISO 8601 datetime)
- *Or alternatively:* `Hours`, `Minutes` — Duration instead of start/end times

**Key optional fields:**
- `TxnDate` — Date of the time activity
- `CustomerRef.value` — Customer the time is for
- `ItemRef.value` — Service item for billing
- `BillableStatus` — `"Billable"`, `"NotBillable"`, `"HasBeenBilled"`
- `Taxable` — `true`/`false`
- `HourlyRate` — Rate for billing
- `Description` — Work description
- `DepartmentRef.value`, `ClassRef.value`

**Read-only fields:** `Id`, `SyncToken`, `MetaData`

**Notes:** TimeActivity records can be used to create Invoice line items for billable time.

---

## Name-List Entities

### Customer

**Endpoint:** `/v3/company/{realmId}/customer`

**Required fields for create:**
- `DisplayName` — Unique display name

**Key optional fields:**
- `GivenName`, `FamilyName`, `MiddleName`, `Suffix`, `Title`
- `CompanyName`
- `PrimaryEmailAddr.Address`
- `PrimaryPhone.FreeFormNumber`
- `Mobile.FreeFormNumber`
- `BillAddr` — Billing address object
- `ShipAddr` — Shipping address object
- `Notes`
- `ParentRef.value` — Parent customer (for sub-customers)
- `Job` — `true` if this is a job/project
- `BillWithParent` — `true` to bill parent customer
- `Taxable` — `true`/`false`
- `DefaultTaxCodeRef.value`
- `PaymentMethodRef.value`
- `SalesTermRef.value`
- `PreferredDeliveryMethod` — `"Print"`, `"Email"`, `"None"`
- `PrintOnCheckName` — Name printed on checks
- `CurrencyRef` — Multi-currency: preferred currency

**Read-only fields:** `Id`, `SyncToken`, `FullyQualifiedName`, `Balance`, `BalanceWithJobs`, `Active`, `MetaData`

**Cannot be deleted** — Set `Active: false` to deactivate.

---

### Vendor

**Endpoint:** `/v3/company/{realmId}/vendor`

**Required fields for create:**
- `DisplayName` — Unique display name

**Key optional fields:**
- `GivenName`, `FamilyName`, `Title`, `Suffix`
- `CompanyName`
- `PrimaryEmailAddr.Address`
- `PrimaryPhone.FreeFormNumber`
- `Mobile.FreeFormNumber`
- `WebAddr.URI`
- `BillAddr`
- `AcctNum` — Account number
- `TaxIdentifier` — Tax ID / SSN
- `Vendor1099` — `true` if 1099 vendor
- `TermRef.value` — Payment terms
- `APAccountRef.value`
- `PrintOnCheckName` — Name printed on checks
- `Notes`
- `CurrencyRef` — Multi-currency: preferred currency

**Read-only fields:** `Id`, `SyncToken`, `Balance`, `Active`, `MetaData`

---

### Employee

**Endpoint:** `/v3/company/{realmId}/employee`

**Required fields for create:**
- `GivenName` — First name
- `FamilyName` — Last name

**Key optional fields:**
- `DisplayName`, `PrintOnCheckName`
- `PrimaryEmailAddr.Address`
- `PrimaryPhone.FreeFormNumber`
- `PrimaryAddr` — Address
- `SSN` — Social Security Number (write-only)
- `BirthDate`, `HiredDate`, `ReleasedDate`
- `EmployeeNumber`
- `BillableTime` — `true` if employee's time is billable

**Read-only fields:** `Id`, `SyncToken`, `Active`, `MetaData`

---

### Item

**Endpoint:** `/v3/company/{realmId}/item`

**Required fields for create:**
- `Name` — Item name (unique within type)
- `Type` — `"Inventory"`, `"Service"`, `"NonInventory"`, `"Group"`, `"Category"`
- `IncomeAccountRef.value` — Income account (for Service/NonInventory)
- For Inventory items also: `AssetAccountRef.value`, `ExpenseAccountRef.value`, `InvStartDate`, `QtyOnHand`

**Key optional fields:**
- `Description` — Sales description
- `PurchaseDesc` — Purchase description
- `UnitPrice` — Sales price
- `PurchaseCost` — Purchase cost
- `Sku`
- `Taxable` — `true`/`false`
- `SalesTaxCodeRef.value`
- `TrackQtyOnHand` — `true` to enable inventory tracking (requires Inventory type)
- `ParentRef.value` — For sub-items

**Read-only fields:** `Id`, `SyncToken`, `FullyQualifiedName`, `Active`, `MetaData`

---

### Account

**Endpoint:** `/v3/company/{realmId}/account`

**Required fields for create:**
- `Name` — Account name
- `AccountType` — One of: `Bank`, `Accounts Receivable`, `Other Current Asset`, `Fixed Asset`, `Other Asset`, `Accounts Payable`, `Credit Card`, `Other Current Liability`, `Long Term Liability`, `Equity`, `Income`, `Cost of Goods Sold`, `Expense`, `Other Income`, `Other Expense`

**Key optional fields:**
- `AccountSubType` — Finer categorization within type
- `Description`
- `AcctNum` — Account number
- `ParentRef.value` — Parent account (for sub-accounts)
- `SubAccount` — `true` if this is a sub-account
- `TaxCodeRef.value`
- `CurrencyRef` — Multi-currency: account currency

**Read-only fields:** `Id`, `SyncToken`, `CurrentBalance`, `CurrentBalanceWithSubAccounts`, `FullyQualifiedName`, `Active`, `Classification`, `MetaData`

**Notes:** `Classification` is auto-derived: `Asset`, `Liability`, `Equity`, `Revenue`, `Expense`.

---

### Class

**Endpoint:** `/v3/company/{realmId}/class`

**Required fields for create:**
- `Name` — Class name

**Key optional fields:**
- `ParentRef.value` — Parent class (for sub-classes)

**Read-only fields:** `Id`, `SyncToken`, `FullyQualifiedName`, `Active`, `MetaData`

---

### Department

**Endpoint:** `/v3/company/{realmId}/department`

**Required fields for create:**
- `Name` — Department name

**Key optional fields:**
- `ParentRef.value` — Parent department
- `SubDepartment` — `true` if sub-department

**Read-only fields:** `Id`, `SyncToken`, `FullyQualifiedName`, `Active`, `MetaData`

---

### TaxCode

**Endpoint:** `/v3/company/{realmId}/taxcode` (READ-ONLY)

**Read-only.** Cannot be created, updated, or deleted via API.

**Key fields:** `Id`, `Name`, `Description`, `Active`, `Taxable`, `TaxGroup`, `SalesTaxRateList`, `PurchaseTaxRateList`

---

### TaxRate

**Endpoint:** `/v3/company/{realmId}/taxrate` (READ-ONLY)

**Read-only.** Cannot be created, updated, or deleted via API.

**Key fields:** `Id`, `Name`, `Description`, `RateValue`, `AgencyRef`, `TaxReturnLineRef`, `Active`

---

### PaymentMethod

**Endpoint:** `/v3/company/{realmId}/paymentmethod`

**Required fields for create:**
- `Name` — Payment method name (e.g., "Wire Transfer")

**Key optional fields:**
- `Type` — `"CREDIT_CARD"` or `"NON_CREDIT_CARD"`

**Read-only fields:** `Id`, `SyncToken`, `Active`, `MetaData`

---

### Term

**Endpoint:** `/v3/company/{realmId}/term`

**Required fields for create:**
- `Name` — Term name (e.g., "Net 30")

**Key optional fields:**
- `Type` — `"STANDARD"` or `"DATE_DRIVEN"`
- `DueDays` — Days until due (for STANDARD)
- `DiscountPercent`, `DiscountDays` — Early payment discount

**Read-only fields:** `Id`, `SyncToken`, `Active`, `MetaData`

---

### TaxAgency

**Endpoint:** `/v3/company/{realmId}/taxagency`

**Required fields for create:**
- `DisplayName` — Tax agency name

**Key optional fields:**
- `TaxTrackedOnSales` — `true` if agency tracks sales tax
- `TaxTrackedOnPurchases` — `true` if agency tracks purchase tax

**Read-only fields:** `Id`, `SyncToken`, `MetaData`

**Notes:** TaxAgency is used with TaxService to create tax codes. Cannot be updated or deleted via API.

---

## Supporting Entities

### Attachable

**Description:** Metadata for a file attachment linked to a transaction or entity.

**Endpoint:** `/v3/company/{realmId}/attachable`

**Required fields for create:**
- `AttachableRef[]` — References to entities this file is attached to
  - `EntityRef.value` — Entity ID
  - `EntityRef.type` — Entity type (e.g., `"Invoice"`, `"Bill"`)

**Key optional fields:**
- `Note` — Description or note
- `FileName` — Original file name
- `ContentType` — MIME type (e.g., `"image/png"`, `"application/pdf"`)
- `Category` — `"Image"`, `"Signature"`, `"Contact Photo"`, `"Receipt"`, `"Document"`, `"Other"`

**Read-only fields:** `Id`, `SyncToken`, `TempDownloadUri`, `Size`, `MetaData`

**Two-step upload process:**
1. `POST /upload` with `multipart/form-data` to upload the file
2. `POST /attachable` to create the Attachable metadata and link to an entity

```
POST /v3/company/{realmId}/upload
Content-Type: multipart/form-data; boundary=----Boundary

------Boundary
Content-Disposition: form-data; name="file_content_01"; filename="receipt.png"
Content-Type: image/png

{binary file data}
------Boundary--
```

---

### Preferences

**Description:** Company-wide settings and preferences.

**Endpoint:** `/v3/company/{realmId}/preferences`

**Operations:** Read (GET), Update (POST) — cannot create or delete.

**Preference sections:**
- `AccountingInfoPrefs` — Fiscal year start, tax year start, tax form, book close date, class/department tracking
- `ProductAndServicesPrefs` — Quantity on hand, quantity with orders, revenue recognition
- `SalesFormsPrefs` — Custom fields, transaction numbers, shipping, discounts, deposits, estimates, ETransactions, IPN
- `EmailMessagesPrefs` — Default messages for invoices, estimates, sales receipts, statements
- `VendorAndPurchasesPrefs` — PO custom fields, default terms, default markup
- `TimeTrackingPrefs` — Use services, billable status, show billable to all
- `TaxPrefs` — Tax calculation partner, group code
- `CurrencyPrefs` — Multi-currency enabled, home currency
- `ReportPrefs` — Report basis (Cash/Accrual), aging method

**Notes:** Use sparse update — only send the preference sections you want to change.

---

### CompanyInfo

**Description:** Company identification and configuration data.

**Endpoint:** `/v3/company/{realmId}/companyinfo/{realmId}`

**Operations:** Read only (GET).

**Key fields:** `CompanyName`, `LegalName`, `CompanyAddr`, `CustomerCommunicationAddr`, `LegalAddr`, `PrimaryPhone`, `CompanyStartDate`, `FiscalYearStartMonth`, `Country`, `Email`, `WebAddr`, `SupportedLanguages`, `NameValue` (custom key-value pairs)

**Notes:** Simplest endpoint for testing API connectivity. Also useful for retrieving company metadata.

---

### TaxService

**Description:** Service endpoint for creating tax codes and rates.

**Endpoint:** `/v3/company/{realmId}/taxservice/taxcode`

**Operations:** Create only (POST) — creates both a TaxCode and its associated TaxRates.

**Required fields for create:**
- `TaxCode` — Name for the new tax code
- `TaxRateDetails[]` — Array of tax rate definitions
  - `TaxRateName` — Name of the tax rate
  - `RateValue` — Tax rate percentage
  - `TaxAgencyId` — ID of the tax agency
  - `TaxApplicableOn` — `"Sales"`, `"Purchase"`, or `"Both"`

**Notes:** This is the only way to programmatically create tax codes. Individual TaxCode and TaxRate entities are read-only.

---

### Batch

**Description:** Execute multiple API operations in a single request.

**Endpoint:** `/v3/company/{realmId}/batch`

**Operations:** POST only.

**Request format:**
```json
{
  "BatchItemRequest": [
    {
      "bId": "1",
      "operation": "create",
      "Invoice": { ... }
    },
    {
      "bId": "2",
      "operation": "query",
      "Query": "SELECT * FROM Customer WHERE Id = '1'"
    },
    {
      "bId": "3",
      "operation": "update",
      "Customer": { "Id": "1", "SyncToken": "0", "sparse": true, "Notes": "Updated" }
    },
    {
      "bId": "4",
      "operation": "delete",
      "Invoice": { "Id": "99", "SyncToken": "0" }
    }
  ]
}
```

**Response format:**
```json
{
  "BatchItemResponse": [
    { "bId": "1", "Invoice": { ... } },
    { "bId": "2", "QueryResponse": { ... } },
    { "bId": "3", "Customer": { ... } },
    { "bId": "4", "Invoice": { "status": "Deleted", "Id": "99" } }
  ]
}
```

**Limits:** Max 30 items per batch. Each item is independent — failures don't roll back others.

**Valid operations:** `create`, `update`, `delete`, `query`

---

### Change Data Capture (CDC)

**Description:** Poll for entities that have changed since a given timestamp.

**Endpoint:** `GET /v3/company/{realmId}/cdc`

**Query parameters:**
- `entities` — Comma-separated entity names (e.g., `Customer,Invoice,Payment`)
- `changedSince` — ISO 8601 timestamp (e.g., `2024-01-01T00:00:00-08:00`)

**Example:**
```
GET /v3/company/{realmId}/cdc?entities=Customer,Invoice&changedSince=2024-01-01T00:00:00-08:00
```

**Response:** Returns arrays of changed entities grouped by type, including deleted entities.

**Limits:** Max 30 days lookback. Store the `time` field from each response for the next poll.

**Notes:** More efficient than querying `MetaData.LastUpdatedTime` on individual entities. Ideal for incremental sync workflows.

---

### ExchangeRate

**Description:** Currency exchange rates for multi-currency companies.

**Endpoint:** `GET /v3/company/{realmId}/exchangerate`

**Query parameters:**
- `sourcecurrencycode` — ISO 4217 currency code (e.g., `EUR`, `GBP`, `CAD`)
- `asofdate` — Date for the rate (YYYY-MM-DD)

**Example:**
```
GET /v3/company/{realmId}/exchangerate?sourcecurrencycode=EUR&asofdate=2024-06-15
```

**Response fields:** `SourceCurrencyCode`, `TargetCurrencyCode`, `Rate`, `AsOfDate`

**Notes:** Only available when multi-currency is enabled in company preferences. Target currency is always the company's home currency.

---

## Common Patterns

### Reference Fields

All entity references use the same format:
```json
{
  "value": "123",
  "name": "Display Name"
}
```
- `value` is required (the entity ID)
- `name` is optional (for readability, ignored by API)

### MetaData Object

Present on all entities:
```json
{
  "MetaData": {
    "CreateTime": "2024-01-15T10:30:00-08:00",
    "LastUpdatedTime": "2024-01-15T10:30:00-08:00"
  }
}
```

### SyncToken

- Present on all entities as a string (e.g., `"0"`, `"1"`, `"2"`)
- Increments on each update
- Must be included in update/delete requests
- Stale SyncToken returns error code 5010

### Address Object

Used for `BillAddr`, `ShipAddr`, `PrimaryAddr`:
```json
{
  "Line1": "123 Main St",
  "Line2": "Suite 100",
  "City": "Mountain View",
  "CountrySubDivisionCode": "CA",
  "PostalCode": "94043",
  "Country": "US"
}
```

### LinkedTxn Array

Used in Payment, Deposit, BillPayment to link to other transactions:
```json
{
  "LinkedTxn": [
    {
      "TxnId": "123",
      "TxnType": "Invoice"
    }
  ]
}
```

Valid `TxnType` values: `Invoice`, `Payment`, `SalesReceipt`, `RefundReceipt`, `Bill`, `BillPayment`, `CreditMemo`, `VendorCredit`, `JournalEntry`, `CashPurchase`, `Estimate`, `PurchaseOrder`, `TimeActivity`

### CustomField Array

Up to 3 custom fields per transaction. Must be defined in QBO UI (Settings > Custom Fields) before use.

```json
{
  "CustomField": [
    {
      "DefinitionId": "1",
      "Name": "Crew #",
      "Type": "StringType",
      "StringValue": "102"
    }
  ]
}
```

- Reference by `DefinitionId` (not by `Name`)
- `Type` is always `"StringType"` — custom fields are strings only
- `Name` is read-only (set in QBO UI)

### Multi-Currency Fields

When multi-currency is enabled on the QBO company, transactions include:

```json
{
  "CurrencyRef": { "value": "EUR", "name": "Euro" },
  "ExchangeRate": 1.08,
  "HomeTotalAmt": 108.00,
  "TotalAmt": 100.00
}
```

- `CurrencyRef.value` — ISO 4217 currency code
- `ExchangeRate` — Auto-populated, can be overridden
- `HomeTotalAmt` — Amount in home currency (read-only, calculated)
- `TotalAmt` — Amount in transaction currency

### Line Item DetailType Reference

Each `Line` object requires a `DetailType` and corresponding detail object:

| DetailType | Used In | Key Fields |
|-----------|---------|------------|
| `SalesItemLineDetail` | Invoice, SalesReceipt, Estimate, CreditMemo, RefundReceipt | `ItemRef`, `UnitPrice`, `Qty`, `TaxCodeRef` |
| `AccountBasedExpenseLineDetail` | Bill, Purchase, PurchaseOrder, VendorCredit | `AccountRef`, `CustomerRef`, `BillableStatus`, `TaxCodeRef` |
| `ItemBasedExpenseLineDetail` | Bill, Purchase, PurchaseOrder, VendorCredit | `ItemRef`, `CustomerRef`, `UnitPrice`, `Qty`, `BillableStatus`, `TaxCodeRef` |
| `JournalEntryLineDetail` | JournalEntry | `PostingType`, `AccountRef`, `Entity`, `ClassRef`, `DepartmentRef` |
| `DepositLineDetail` | Deposit | `AccountRef`, `Entity` |
| `DiscountLineDetail` | Invoice, Estimate, CreditMemo | `PercentBased`, `DiscountPercent`, `DiscountAccountRef` |
| `SubTotalLineDetail` | Invoice, Estimate | (system-generated subtotal line) |
| `DescriptionOnly` | Invoice, Estimate | `Description` (no amount) |
