# Quickstart Guide

This guide gets you from zero to a working Google Apps Script project managed by `gas-skill` in about 10 minutes.

## Prerequisites

You need the following installed on your Debian/Linux system:

- **Python 3.11+**
- **Node.js 18+** and npm
- **Git 2.39+**
- **GitHub CLI** (`gh`)
- **clasp** (Google Apps Script CLI)
- A **Google account** with Apps Script API enabled
- A **GitHub account** with a repository ready

### Install missing tools

```bash
# System packages
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git curl jq

# Node.js (if not installed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# clasp
sudo npm install -g @google/clasp

# GitHub CLI
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) \
    signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] \
    https://cli.github.com/packages stable main" \
    | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt-get update
sudo apt-get install -y gh
```

## Step 1: Set up Google Cloud

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the **Apps Script API**: APIs & Services > Library > search "Apps Script API" > Enable
4. Configure an **OAuth consent screen**: APIs & Services > OAuth consent screen > External > add your email as a test user
5. Create **OAuth credentials**: APIs & Services > Credentials > Create Credentials > OAuth Client ID > Desktop App > Download the JSON file

## Step 2: Authenticate

```bash
# Authenticate clasp with your OAuth credentials
clasp login --creds /path/to/credentials.json
# A browser window will open. Approve the permissions.
# This stores a token at ~/.clasprc.json

# Authenticate GitHub CLI
gh auth login
# Follow the prompts to authenticate
```

## Step 3: Install gas-skill

```bash
# Navigate to your project directory
cd /path/to/your/project

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install gas-skill in development mode
pip install -e ".[dev]"

# Verify it works
gas-skill --help
```

## Step 4: Run preflight checks

```bash
gas-skill preflight
```

You should see JSON output with check results. All items should show `"passed": true`. If any fail, fix the issue indicated in the `"detail"` field before continuing.

Example output:
```json
{
  "all_passed": true,
  "checks": [
    {"name": "python", "passed": true, "detail": "3.13.5"},
    {"name": "nodejs", "passed": true, "detail": "v20.19.2"},
    {"name": "clasp", "passed": true, "detail": "2.4.1"},
    {"name": "git", "passed": true, "detail": "git version 2.47.3"},
    {"name": "gh_cli", "passed": true, "detail": "..."},
    {"name": "clasp_auth", "passed": true, "detail": "/home/user/.clasprc.json"},
    {"name": "project_config", "passed": true, "detail": "..."},
    {"name": "manifest", "passed": true, "detail": "Manifest is valid"}
  ]
}
```

## Step 5: Initialize a project

Create a new GitHub repository first, then:

```bash
gas-skill init \
  --type sheets \
  --title "My Spreadsheet Automation" \
  --github-url git@github.com:youruser/my-gas-project.git
```

This command:
- Creates two Apps Script projects (production and development)
- Saves their configurations as `.clasp.prod.json` and `.clasp.dev.json`
- Generates the project directory structure (`src/`, `tests/`, `docs/`)
- Writes starter files: `Code.js`, `Tests.js`, `appsscript.json`, `gas_skill.toml`
- Initializes Git with `main` and `develop` branches
- Pushes both branches to GitHub

Supported `--type` values: `sheets`, `docs`, `slides`, `forms`, `webapp`, `api`

## Step 6: Create a feature branch and write code

```bash
# Create a feature branch (branched from develop)
gas-skill branch create my-first-feature
```

Now edit `src/Code.js` with your Apps Script code and add tests in `src/Tests.js`:

```javascript
// src/Code.js
function getGreeting(name) {
  return "Hello, " + name + "!";
}

// src/Tests.js (add to existing file, after the example tests)
function test_greeting() {
  var result = getGreeting("World");
  return assertEqual(result, "Hello, World!", "greeting function");
}
```

## Step 7: Commit and test

```bash
# Commit your changes
gas-skill commit -m "add greeting function" --type feat --scope core

# Push to Apps Script and run tests
gas-skill test-loop
```

If the test-loop reports success:
```json
{
  "success": true,
  "total_iterations": 1,
  "branch": "feature/my-first-feature",
  "final_commit": "abc1234"
}
```

If it reports failure, read the `action_needed` and `error_detail` fields, fix your code, commit, and run `test-loop` again.

## Step 8: Merge and release

```bash
# Merge your feature into develop
gas-skill merge --from feature/my-first-feature --to develop

# When ready for production, release from develop
gas-skill release --version 1.0.0 --summary "Initial release with greeting function"
```

## What's next?

- Read the [User Guide](user-guide.md) for a complete reference of all commands
- Check `gas-skill <command> --help` for any command's options
- Look at `gas_skill.toml` to customize settings like max retries, branch prefixes, etc.
