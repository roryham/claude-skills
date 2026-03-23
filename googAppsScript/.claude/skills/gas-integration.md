---
name: Google Apps Script Integration
description: >
  Manage Google Apps Script projects with automated push, test, debug,
  and deploy workflows using Git-based version control. All operations
  go through the gas-skill Python CLI tool.
trigger: >
  Activate when the user asks to work with Google Apps Script, GAS,
  Apps Script, clasp, or mentions working with spreadsheet/document
  automation via Google services.
---

# Google Apps Script Integration Skill

## Overview

You have access to a Python CLI tool called `gas-skill` that manages
the full lifecycle of Google Apps Script development. All GAS operations
MUST go through this tool — never call `clasp` or `git` directly.

## Quick Reference

```bash
# Check prerequisites
gas-skill preflight

# Project status
gas-skill status

# Create a feature branch
gas-skill branch create <name>

# Commit changes
gas-skill commit -m "<message>" --type <feat|fix|test|...> [--scope <scope>]

# Push to Apps Script and run tests
gas-skill test-loop

# Merge when tests pass
gas-skill merge --from <branch> --to develop

# Release to production
gas-skill release --version <X.Y.Z> --summary "<text>"
```

## Workflow

1. **Start**: `gas-skill preflight` to verify environment
2. **Branch**: `gas-skill branch create <feature-name>` from develop
3. **Code**: Write/edit `.js` files in `src/`
4. **Commit**: `gas-skill commit -m "description" --type feat`
5. **Test**: `gas-skill test-loop` — pushes to GAS, runs tests, reports results
6. **Fix**: If tests fail, read the JSON error, fix code, commit, test-loop again
7. **Merge**: `gas-skill merge --from feature/<name> --to develop`
8. **Release**: `gas-skill release --version X.Y.Z --summary "..."`

## Important Rules

- NEVER commit directly to `main` — all work happens on feature branches
- NEVER call `clasp` or `git` directly — always use `gas-skill`
- All output is structured JSON — parse it to understand results
- The test-loop does ONE cycle per call — you drive the retry loop
- Every fix attempt is committed to Git for full audit trail
