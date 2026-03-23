# QuickBooks Online OAuth 2.0 Reference

## Endpoints

| Purpose | URL |
|---------|-----|
| Authorization | `https://appcenter.intuit.com/connect/oauth2` |
| Token Exchange | `https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer` |
| Revocation | `https://developer.api.intuit.com/v2/oauth2/tokens/revoke` |
| User Info | `https://accounts.platform.intuit.com/v1/openid_connect/userinfo` |

## Scopes

| Scope | Access |
|-------|--------|
| `com.intuit.quickbooks.accounting` | Full QBO read/write |
| `com.intuit.quickbooks.payment` | Payment processing |
| `openid` | OpenID Connect (user info) |
| `profile` | User profile info |
| `email` | User email |

For QBO API access, use: `com.intuit.quickbooks.accounting`

## Authorization Code Flow

### Step 1: Redirect User to Authorization URL

```
https://appcenter.intuit.com/connect/oauth2
  ?client_id={CLIENT_ID}
  &scope=com.intuit.quickbooks.accounting
  &redirect_uri={REDIRECT_URI}
  &response_type=code
  &state={CSRF_STATE_TOKEN}
```

**Parameters:**
- `client_id` — From Intuit Developer portal
- `scope` — Space-separated scopes
- `redirect_uri` — Must exactly match portal configuration
- `response_type` — Always `code`
- `state` — Random string for CSRF protection (verify on callback)

### Step 2: Handle Callback

User authorizes, Intuit redirects to:
```
{REDIRECT_URI}?code={AUTH_CODE}&state={STATE}&realmId={COMPANY_ID}
```

**Critical:** Verify `state` matches what you sent. Save `realmId` — it identifies the QuickBooks company.

### Step 3: Exchange Code for Tokens

```
POST https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer
Content-Type: application/x-www-form-urlencoded
Authorization: Basic {base64(CLIENT_ID:CLIENT_SECRET)}

grant_type=authorization_code
&code={AUTH_CODE}
&redirect_uri={REDIRECT_URI}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "AB11...",
  "token_type": "bearer",
  "expires_in": 3600,
  "x_refresh_token_expires_in": 8726400
}
```

| Field | Value |
|-------|-------|
| `access_token` | Valid for 1 hour (3600 seconds) |
| `refresh_token` | Valid for 100 days (8726400 seconds) |
| `x_refresh_token_expires_in` | Refresh token lifetime in seconds |

### Step 4: Use Access Token

```
GET /v3/company/{realmId}/companyinfo/{realmId}
Authorization: Bearer {access_token}
Accept: application/json
```

## Token Refresh Flow

```
POST https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer
Content-Type: application/x-www-form-urlencoded
Authorization: Basic {base64(CLIENT_ID:CLIENT_SECRET)}

grant_type=refresh_token
&refresh_token={REFRESH_TOKEN}
```

**Response:** Same format as initial token exchange. Both `access_token` and `refresh_token` are replaced — store the new values.

### Proactive Refresh Strategy

- Check token expiry before each API call
- Refresh 5 minutes before expiry (buffer for clock skew)
- Calculate expiry: `token_expiry = Date.now() + (expires_in * 1000)`
- Store expiry timestamp alongside tokens

```javascript
function isTokenExpired() {
  var expiry = getStoredExpiry();
  var bufferMs = 5 * 60 * 1000; // 5 minutes
  return Date.now() >= (expiry - bufferMs);
}
```

## 100-Day Refresh Token Expiry

The refresh token expires after **100 days**. After expiry, the user must re-authorize completely.

**Mitigation strategies:**
1. **Proactive refresh:** Refresh tokens weekly even if access token is still valid — each refresh resets the 100-day clock
2. **Expiry tracking:** Store `x_refresh_token_expires_in` and warn users before expiry
3. **Re-auth flow:** Implement a clean re-authorization path for when tokens expire

**Important:** Each token refresh issues a NEW refresh token with a fresh 100-day expiry. The old refresh token is invalidated.

## Token Revocation

```
POST https://developer.api.intuit.com/v2/oauth2/tokens/revoke
Content-Type: application/json
Authorization: Basic {base64(CLIENT_ID:CLIENT_SECRET)}

{
  "token": "{ACCESS_TOKEN_OR_REFRESH_TOKEN}"
}
```

Revoking the refresh token also revokes its associated access token.

## Token Storage Best Practices

### Server-Side Applications
- Store encrypted in database
- Never expose in client-side code or logs
- Use environment variables for client credentials

### Google Apps Script
- Use `PropertiesService.getUserProperties()` for per-user tokens
- Use `PropertiesService.getScriptProperties()` for shared credentials
- Property keys: `qb_access_token`, `qb_refresh_token`, `qb_token_expiry`, `qb_realm_id`

### Never Store
- Tokens in source code or version control
- Tokens in URL parameters
- Client secret in client-side code

## CSRF State Token Protection

Generate a unique, unpredictable state value per authorization request:

```javascript
// Google Apps Script
var state = Utilities.getUuid();
PropertiesService.getUserProperties().setProperty('oauth_state', state);
```

On callback, verify:
```javascript
var savedState = PropertiesService.getUserProperties().getProperty('oauth_state');
if (receivedState !== savedState) {
  throw new Error('CSRF state mismatch');
}
```

## Sandbox vs Production

| Aspect | Sandbox | Production |
|--------|---------|------------|
| OAuth App | Separate app in developer portal | Separate app |
| Client ID/Secret | Different credentials | Different credentials |
| API Base URL | `sandbox-quickbooks.api.intuit.com` | `quickbooks.api.intuit.com` |
| Authorization URL | Same (`appcenter.intuit.com/connect/oauth2`) | Same |
| Token URL | Same (`oauth.platform.intuit.com/...`) | Same |
| Data | Test data only | Live company data |
| realmId | Sandbox company ID | Production company ID |

**Important:** Sandbox and production use the same OAuth authorization and token endpoints, but different API base URLs and different OAuth app credentials.

## Redirect URI Requirements

- Must be HTTPS (except `localhost` for development)
- Must exactly match the URI registered in the Intuit Developer portal
- No wildcard or pattern matching
- Google Apps Script: Use `ScriptApp.getService().getUrl()` for the web app URL
- Common format: `https://script.google.com/macros/d/{SCRIPT_ID}/usercallback`

## Common OAuth Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `invalid_client` | Wrong client ID/secret | Verify credentials match environment |
| `invalid_grant` | Auth code expired or already used | Auth codes are single-use and expire in 5 minutes |
| `invalid_redirect_uri` | Redirect URI mismatch | URI must exactly match portal registration |
| `access_denied` | User denied authorization | Prompt user again |
| `unauthorized_client` | App not approved | Complete Intuit app review |
| 401 on API call | Token expired | Refresh the access token |
