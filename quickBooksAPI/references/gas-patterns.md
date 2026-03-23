# Google Apps Script Patterns for QuickBooks Online

Patterns derived from production QBO integrations using Google Apps Script.

## UrlFetchApp API Calls

### GET Request (Query / Read)

```javascript
function qboGet(endpoint) {
  var token = getValidAccessToken();
  var realmId = PropertiesService.getUserProperties().getProperty('qb_realm_id');
  var baseUrl = getBaseUrl(); // sandbox or production

  var url = baseUrl + '/v3/company/' + realmId + '/' + endpoint;
  if (url.indexOf('?') === -1) {
    url += '?minorversion=75';
  } else {
    url += '&minorversion=75';
  }

  var options = {
    method: 'get',
    headers: {
      'Authorization': 'Bearer ' + token,
      'Accept': 'application/json'
    },
    muteHttpExceptions: true
  };

  var response = UrlFetchApp.fetch(url, options);
  var code = response.getResponseCode();

  if (code === 401) {
    token = refreshAccessToken();
    options.headers['Authorization'] = 'Bearer ' + token;
    response = UrlFetchApp.fetch(url, options);
    code = response.getResponseCode();
  }

  if (code !== 200) {
    throw new Error('QBO API error ' + code + ': ' + response.getContentText());
  }

  return JSON.parse(response.getContentText());
}
```

### POST Request (Create / Update)

```javascript
function qboPost(endpoint, payload) {
  var token = getValidAccessToken();
  var realmId = PropertiesService.getUserProperties().getProperty('qb_realm_id');
  var baseUrl = getBaseUrl();

  var url = baseUrl + '/v3/company/' + realmId + '/' + endpoint + '?minorversion=75';

  var options = {
    method: 'post',
    headers: {
      'Authorization': 'Bearer ' + token,
      'Accept': 'application/json'
    },
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  var response = UrlFetchApp.fetch(url, options);
  var code = response.getResponseCode();

  if (code === 401) {
    token = refreshAccessToken();
    options.headers['Authorization'] = 'Bearer ' + token;
    response = UrlFetchApp.fetch(url, options);
    code = response.getResponseCode();
  }

  if (code !== 200) {
    throw new Error('QBO API error ' + code + ': ' + response.getContentText());
  }

  return JSON.parse(response.getContentText());
}
```

### Query Helper

```javascript
function qboQuery(queryString) {
  var encodedQuery = encodeURIComponent(queryString);
  return qboGet('query?query=' + encodedQuery);
}
```

## Properties Service for Token Storage

### Storing Tokens

```javascript
function storeTokens(accessToken, refreshToken, expiresIn) {
  var props = PropertiesService.getUserProperties();
  var expiry = new Date().getTime() + (expiresIn * 1000);

  props.setProperties({
    'qb_access_token': accessToken,
    'qb_refresh_token': refreshToken,
    'qb_token_expiry': expiry.toString()
  });
}
```

### Retrieving Tokens

```javascript
function getValidAccessToken() {
  var props = PropertiesService.getUserProperties();
  var expiry = parseInt(props.getProperty('qb_token_expiry'), 10);
  var bufferMs = 5 * 60 * 1000; // 5-minute buffer

  if (new Date().getTime() >= (expiry - bufferMs)) {
    return refreshAccessToken();
  }

  return props.getProperty('qb_access_token');
}
```

### Credential Storage (Separate Sandbox/Production)

```javascript
function getCredentials() {
  var props = PropertiesService.getUserProperties();
  var env = props.getProperty('qb_environment') || 'sandbox';

  return {
    clientId: props.getProperty('qb_client_id_' + env),
    clientSecret: props.getProperty('qb_client_secret_' + env),
    environment: env
  };
}
```

## Token Refresh Implementation

```javascript
function refreshAccessToken() {
  var props = PropertiesService.getUserProperties();
  var refreshToken = props.getProperty('qb_refresh_token');
  var creds = getCredentials();

  var authHeader = Utilities.base64Encode(creds.clientId + ':' + creds.clientSecret);

  var response = UrlFetchApp.fetch(
    'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer',
    {
      method: 'post',
      headers: {
        'Authorization': 'Basic ' + authHeader,
        'Accept': 'application/json'
      },
      contentType: 'application/x-www-form-urlencoded',
      payload: 'grant_type=refresh_token&refresh_token=' + refreshToken,
      muteHttpExceptions: true
    }
  );

  if (response.getResponseCode() !== 200) {
    throw new Error('Token refresh failed: ' + response.getContentText());
  }

  var data = JSON.parse(response.getContentText());
  storeTokens(data.access_token, data.refresh_token, data.expires_in);

  return data.access_token;
}
```

## OAuth 2.0 Authorization Flow in GAS

### Step 1: Generate Authorization URL

```javascript
function getAuthorizationUrl() {
  var creds = getCredentials();
  var state = Utilities.getUuid();
  var redirectUri = ScriptApp.getService().getUrl();

  PropertiesService.getUserProperties().setProperty('oauth_state', state);

  return 'https://appcenter.intuit.com/connect/oauth2'
    + '?client_id=' + creds.clientId
    + '&scope=com.intuit.quickbooks.accounting'
    + '&redirect_uri=' + encodeURIComponent(redirectUri)
    + '&response_type=code'
    + '&state=' + state;
}
```

### Step 2: Handle Callback

```javascript
function doGet(e) {
  if (e.parameter.code) {
    return handleOAuthCallback(e);
  }
  // ... normal web app response
}

function handleOAuthCallback(e) {
  var props = PropertiesService.getUserProperties();
  var savedState = props.getProperty('oauth_state');

  if (e.parameter.state !== savedState) {
    return HtmlService.createHtmlOutput('Error: State mismatch (CSRF protection)');
  }

  var realmId = e.parameter.realmId;
  props.setProperty('qb_realm_id', realmId);

  // Exchange code for tokens
  var creds = getCredentials();
  var authHeader = Utilities.base64Encode(creds.clientId + ':' + creds.clientSecret);
  var redirectUri = ScriptApp.getService().getUrl();

  var response = UrlFetchApp.fetch(
    'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer',
    {
      method: 'post',
      headers: {
        'Authorization': 'Basic ' + authHeader,
        'Accept': 'application/json'
      },
      contentType: 'application/x-www-form-urlencoded',
      payload: 'grant_type=authorization_code'
        + '&code=' + e.parameter.code
        + '&redirect_uri=' + encodeURIComponent(redirectUri),
      muteHttpExceptions: true
    }
  );

  var data = JSON.parse(response.getContentText());
  storeTokens(data.access_token, data.refresh_token, data.expires_in);

  return HtmlService.createHtmlOutput('Authorization successful! You can close this tab.');
}
```

## Rate Limiting with Utilities.sleep()

```javascript
var API_DELAY_MS = 150; // ~400 requests/min (under 500/min limit)

function qboGetWithRateLimit(endpoint) {
  Utilities.sleep(API_DELAY_MS);
  return qboGet(endpoint);
}

function qboQueryAll(entityName, whereClause) {
  var allResults = [];
  var startPosition = 1;
  var maxResults = 1000;

  do {
    var query = 'SELECT * FROM ' + entityName;
    if (whereClause) {
      query += ' WHERE ' + whereClause;
    }
    query += ' STARTPOSITION ' + startPosition + ' MAXRESULTS ' + maxResults;

    Utilities.sleep(API_DELAY_MS);
    var response = qboQuery(query);
    var entities = response.QueryResponse[entityName] || [];
    allResults = allResults.concat(entities);
    startPosition += maxResults;
  } while (entities.length === maxResults);

  return allResults;
}
```

### Paginated Invoice and SalesReceipt Queries

```javascript
// All invoices in a date range (auto-paginates)
var invoices = qboQueryAll('Invoice',
  "TxnDate >= '2024-01-01' AND TxnDate <= '2024-12-31'");

// All sales receipts in a date range (auto-paginates)
var salesReceipts = qboQueryAll('SalesReceipt',
  "TxnDate >= '2024-01-01' AND TxnDate <= '2024-01-31'");

// Unpaid invoices (auto-paginates)
var unpaid = qboQueryAll('Invoice', 'Balance > 0');
```

**Important:** The `entityName` passed to `qboQueryAll` must exactly match the QBO response key — `'Invoice'` not `'Invoices'`, `'SalesReceipt'` not `'SalesReceipts'`. A mismatch causes `response.QueryResponse[entityName]` to return `undefined`, which the `|| []` fallback silently turns into an empty array, breaking the pagination loop on the first iteration.

## Error Handling and Retry

```javascript
function qboGetWithRetry(endpoint, maxRetries) {
  maxRetries = maxRetries || 3;
  var lastError;

  for (var attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return qboGet(endpoint);
    } catch (e) {
      lastError = e;
      var msg = e.message || '';

      // Don't retry client errors (4xx except 429)
      if (msg.indexOf('400') !== -1 || msg.indexOf('404') !== -1) {
        throw e;
      }

      // Retry on 429 (rate limit) and 5xx (server errors)
      if (attempt < maxRetries) {
        var delay = Math.pow(2, attempt) * 1000; // Exponential backoff
        Logger.log('QBO retry ' + attempt + '/' + maxRetries + ' after ' + delay + 'ms');
        Utilities.sleep(delay);
      }
    }
  }

  throw lastError;
}
```

## Sheet Integration Patterns

### Reading Data from Sheet

```javascript
function getCSVDataFromSheet(sheetName) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
  if (!sheet) throw new Error('Sheet "' + sheetName + '" not found');

  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var rows = [];

  for (var i = 1; i < data.length; i++) {
    var row = {};
    for (var j = 0; j < headers.length; j++) {
      row[headers[j]] = data[i][j];
    }
    rows.push(row);
  }

  return rows;
}
```

### Writing Results to Sheet

```javascript
function writeResultsToSheet(sheetName, results, headers) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
  }
  sheet.clear();

  // Write headers
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');

  // Write data
  if (results.length > 0) {
    var data = results.map(function(row) {
      return headers.map(function(h) { return row[h] || ''; });
    });
    sheet.getRange(2, 1, data.length, headers.length).setValues(data);
  }
}
```

### Color-Coded Status

```javascript
function colorRow(sheet, row, status) {
  var range = sheet.getRange(row, 1, 1, sheet.getLastColumn());
  switch (status) {
    case 'matched':
      range.setBackground('#d9ead3'); // Green
      break;
    case 'csv_only':
      range.setBackground('#fff2cc'); // Yellow
      break;
    case 'qb_only':
      range.setBackground('#f4cccc'); // Red
      break;
    case 'error':
      range.setBackground('#ea9999'); // Dark red
      break;
  }
}
```

## Menu and Dialog Creation

```javascript
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  var menu = ui.createMenu('QuickBooks');

  menu.addItem('Connect to QuickBooks', 'showAuthDialog');
  menu.addItem('Test Connection', 'testConnection');
  menu.addSeparator();
  menu.addItem('Run Matching', 'runMatching');
  menu.addItem('Create Deposits', 'createDeposits');
  menu.addSeparator();
  menu.addItem('Settings', 'showSettings');

  // Dynamic items based on environment
  var env = PropertiesService.getUserProperties().getProperty('qb_environment') || 'sandbox';
  menu.addItem('Switch to ' + (env === 'sandbox' ? 'Production' : 'Sandbox'), 'toggleEnvironment');

  menu.addToUi();
}

function showAuthDialog() {
  var url = getAuthorizationUrl();
  var html = HtmlService.createHtmlOutput(
    '<p>Click the link below to authorize QuickBooks access:</p>'
    + '<p><a href="' + url + '" target="_blank">Authorize QuickBooks</a></p>'
  ).setWidth(400).setHeight(200);

  SpreadsheetApp.getUi().showModalDialog(html, 'QuickBooks Authorization');
}

function showSettings() {
  var html = HtmlService.createHtmlOutputFromFile('SettingsDialog')
    .setWidth(500)
    .setHeight(400);
  SpreadsheetApp.getUi().showModalDialog(html, 'QuickBooks Settings');
}
```

## 6-Minute Execution Timeout Handling

Google Apps Script has a 6-minute execution limit. For large operations:

### Batch Processing with Continuation

```javascript
function processInBatches(items, processFn, batchName) {
  var props = PropertiesService.getUserProperties();
  var startIndex = parseInt(props.getProperty(batchName + '_index') || '0', 10);
  var results = JSON.parse(props.getProperty(batchName + '_results') || '[]');
  var startTime = new Date().getTime();
  var timeLimit = 5 * 60 * 1000; // 5 minutes (1 min buffer)

  for (var i = startIndex; i < items.length; i++) {
    // Check time remaining
    if (new Date().getTime() - startTime > timeLimit) {
      // Save progress and schedule continuation
      props.setProperty(batchName + '_index', i.toString());
      props.setProperty(batchName + '_results', JSON.stringify(results));

      // Create a trigger to continue
      ScriptApp.newTrigger('continueProcessing')
        .timeBased()
        .after(1000)
        .create();

      SpreadsheetApp.getActiveSpreadsheet().toast(
        'Processed ' + i + '/' + items.length + '. Continuing automatically...',
        'In Progress'
      );
      return;
    }

    var result = processFn(items[i]);
    results.push(result);
    Utilities.sleep(API_DELAY_MS);
  }

  // Cleanup
  props.deleteProperty(batchName + '_index');
  props.deleteProperty(batchName + '_results');

  SpreadsheetApp.getActiveSpreadsheet().toast(
    'Completed processing ' + items.length + ' items.',
    'Done'
  );

  return results;
}
```

### Progress Tracking with Toast

```javascript
function showProgress(current, total, operation) {
  SpreadsheetApp.getActiveSpreadsheet().toast(
    operation + ': ' + current + ' of ' + total,
    'Progress',
    3
  );
}
```

## Customer Caching Optimization

Instead of fetching customer details per-transaction, build a cache upfront:

```javascript
function buildCustomerCache() {
  var customers = qboQueryAll('Customer', "Active = true");
  var cache = {};

  customers.forEach(function(customer) {
    cache[customer.Id] = {
      id: customer.Id,
      displayName: customer.DisplayName,
      email: customer.PrimaryEmailAddr ? customer.PrimaryEmailAddr.Address : null,
      balance: customer.Balance
    };
  });

  return cache;
}

// Usage: look up customer in O(1) instead of making an API call
function getCustomerFromCache(cache, customerId) {
  return cache[customerId] || null;
}
```

**Performance impact:** For matching operations involving 100+ transactions, caching reduces API calls from N (one per transaction) to 1 (single bulk query).

## Environment Switching (Sandbox/Production)

```javascript
function getBaseUrl() {
  var env = PropertiesService.getUserProperties().getProperty('qb_environment') || 'sandbox';
  if (env === 'production') {
    return 'https://quickbooks.api.intuit.com';
  }
  return 'https://sandbox-quickbooks.api.intuit.com';
}

function toggleEnvironment() {
  var props = PropertiesService.getUserProperties();
  var current = props.getProperty('qb_environment') || 'sandbox';
  var newEnv = current === 'sandbox' ? 'production' : 'sandbox';

  props.setProperty('qb_environment', newEnv);

  // Clear tokens (different environment = different auth)
  props.deleteProperty('qb_access_token');
  props.deleteProperty('qb_refresh_token');
  props.deleteProperty('qb_token_expiry');
  props.deleteProperty('qb_realm_id');

  SpreadsheetApp.getUi().alert(
    'Switched to ' + newEnv + ' environment.\n\nYou need to re-authorize with QuickBooks.'
  );

  // Rebuild menu to reflect new environment
  onOpen();
}
```

## Connection Testing

```javascript
function testConnection() {
  try {
    var realmId = PropertiesService.getUserProperties().getProperty('qb_realm_id');
    if (!realmId) {
      SpreadsheetApp.getUi().alert('Not connected. Please authorize first.');
      return;
    }

    var result = qboGet('companyinfo/' + realmId);
    var company = result.CompanyInfo;
    var env = PropertiesService.getUserProperties().getProperty('qb_environment') || 'sandbox';

    SpreadsheetApp.getUi().alert(
      'Connected to QuickBooks (' + env + ')\n\n'
      + 'Company: ' + company.CompanyName + '\n'
      + 'Realm ID: ' + realmId
    );
  } catch (e) {
    SpreadsheetApp.getUi().alert('Connection failed: ' + e.message);
  }
}
```

## Duplicate-Aware Matching

Customers may accidentally submit duplicate orders, resulting in multiple SalesReceipts, Invoices, or Deposits with the same amount, date, and customer. Never assume a single match — always collect all candidates and surface duplicates for user review.

### Finding All Matches (Not Just the First)

```javascript
/**
 * Find all QBO transactions matching search criteria.
 * Returns ALL matches so duplicates are visible — never short-circuits on first hit.
 *
 * @param {string} entityName - 'SalesReceipt', 'Invoice', 'Deposit', etc.
 * @param {string} whereClause - WHERE clause (without the WHERE keyword)
 * @param {function} filterFn - Optional client-side filter for criteria not queryable via API
 * @returns {object[]} All matching entities
 */
function findAllMatches(entityName, whereClause, filterFn) {
  var allEntities = qboQueryAll(entityName, whereClause);

  if (filterFn) {
    allEntities = allEntities.filter(filterFn);
  }

  return allEntities; // Always return ALL matches, not just [0]
}
```

### Matching by Customer + Amount + Date with Duplicate Detection

```javascript
/**
 * Search for transactions matching a CSV row, flagging duplicates.
 * Returns { matches: [], isDuplicate: boolean }
 */
function findMatchingReceipts(csvRow, startDate, endDate) {
  var allReceipts = qboQueryAll('SalesReceipt',
    "TxnDate >= '" + startDate + "' AND TxnDate <= '" + endDate + "'");

  var matches = allReceipts.filter(function(receipt) {
    var amountMatch = amountsMatch(receipt.TotalAmt, csvRow.amount);
    var emailMatch = false;

    if (csvRow.email && receipt.BillEmail) {
      emailMatch = csvRow.email.toLowerCase() === receipt.BillEmail.Address.toLowerCase();
    }

    return amountMatch && emailMatch;
  });

  return {
    matches: matches,
    isDuplicate: matches.length > 1
  };
}
```

### Surfacing Duplicates to the User

```javascript
/**
 * Process matches and flag duplicates in the results sheet.
 * Duplicates get a distinct color and are never auto-processed.
 */
function processWithDuplicateHandling(csvRows, qboMatches, resultsSheet) {
  for (var i = 0; i < csvRows.length; i++) {
    var result = qboMatches[i];
    var row = i + 2; // 1-based, skip header

    if (result.matches.length === 0) {
      colorRow(resultsSheet, row, 'csv_only');
      resultsSheet.getRange(row, getStatusCol()).setValue('No match');

    } else if (result.isDuplicate) {
      // NEVER auto-process duplicates — flag for manual review
      colorRow(resultsSheet, row, 'duplicate');
      resultsSheet.getRange(row, getStatusCol()).setValue(
        'DUPLICATE: ' + result.matches.length + ' matches found — review manually');

      // List the duplicate IDs so the user can inspect each one
      var ids = result.matches.map(function(m) { return m.Id; }).join(', ');
      resultsSheet.getRange(row, getNotesCol()).setValue('QBO IDs: ' + ids);

    } else {
      colorRow(resultsSheet, row, 'matched');
      resultsSheet.getRange(row, getStatusCol()).setValue('Matched');
      resultsSheet.getRange(row, getNotesCol()).setValue('QBO ID: ' + result.matches[0].Id);
    }
  }
}
```

### Duplicate Color Coding

Add a distinct color for duplicates alongside existing status colors:

```javascript
function colorRow(sheet, row, status) {
  var range = sheet.getRange(row, 1, 1, sheet.getLastColumn());
  switch (status) {
    case 'matched':
      range.setBackground('#d9ead3'); // Green — single match
      break;
    case 'duplicate':
      range.setBackground('#d9d2e9'); // Purple — multiple matches, needs review
      break;
    case 'csv_only':
      range.setBackground('#fff2cc'); // Yellow — no QBO match
      break;
    case 'qb_only':
      range.setBackground('#f4cccc'); // Red — in QBO but not in CSV
      break;
    case 'error':
      range.setBackground('#ea9999'); // Dark red — error
      break;
  }
}
```

### Confirmation Dialog for Duplicate Resolution

```javascript
/**
 * When a user selects a row flagged as duplicate, show the candidates
 * and let them pick which one to use (or skip).
 */
function resolveDuplicate(qboIds, entityName) {
  var details = qboIds.map(function(id) {
    var entity = qboGet(entityName.toLowerCase() + '/' + id);
    var data = entity[entityName];
    return 'ID ' + data.Id
      + ' | $' + data.TotalAmt
      + ' | ' + data.TxnDate
      + ' | DocNum: ' + (data.DocNumber || 'N/A')
      + ' | Customer: ' + (data.CustomerRef ? data.CustomerRef.name : 'N/A');
  });

  var msg = 'Multiple matches found. Select the correct one:\n\n'
    + details.map(function(d, i) { return (i + 1) + ') ' + d; }).join('\n')
    + '\n\nEnter the number (or 0 to skip):';

  var response = SpreadsheetApp.getUi().prompt('Resolve Duplicate', msg,
    SpreadsheetApp.getUi().ButtonSet.OK_CANCEL);

  if (response.getSelectedButton() === SpreadsheetApp.getUi().Button.CANCEL) {
    return null;
  }

  var choice = parseInt(response.getResponseText(), 10);
  if (choice > 0 && choice <= qboIds.length) {
    return qboIds[choice - 1];
  }
  return null;
}
```

## Amount Parsing and Comparison

```javascript
function parseAmount(value) {
  if (typeof value === 'number') return value;
  if (!value) return 0;
  return parseFloat(String(value).replace(/[$,]/g, '')) || 0;
}

function amountsMatch(a, b, tolerance) {
  tolerance = tolerance || 0.01;
  return Math.abs(parseAmount(a) - parseAmount(b)) <= tolerance;
}
```

## Email Extraction from Transaction Fields

```javascript
function extractEmail(text) {
  if (!text) return null;
  var match = String(text).match(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/);
  return match ? match[0].toLowerCase() : null;
}
```
