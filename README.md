# MkweliAML - Open-Source Browser-Based AML/KYC Sanctions Screening Tool

MkweliAML is a lightweight, privacy-focused Anti-Money Laundering (AML) and Know Your Customer (KYC) compliance tool. Designed for NGOs, small organizations, and compliance teams in resource-limited environments, it runs locally in your browser via a simple Python server. No cloud dependencies, no internet required after setup—ensuring data privacy.

Key features:
- **Setup Wizard**: Guides through master password setup, sanctions list import, and first client addition.
- **Sanctions Management**: Import consolidated lists from XLSX (e.g., UN, UK, US/EU sources) or fetch from GitHub. Auto-parses and stores in local SQLite DB.
- **Client Management**: Add/delete clients, perform fuzzy-matched sanctions checks (using fuzzywuzzy for accurate name matching), update risk scores.
- **Reports**: Generate HTML/PDF reports with SHA-256 hashes for integrity, match details, and source documentation.
- **Dashboard**: Stats on clients, flagged cases, recent activity, and list status.
- **Security**: Master password hashing, failed login lockouts, audit logs.
- **Cross-Platform**: Runs on Ubuntu, Windows, Mac via simple scripts.

Built with assistance from Grok AI for ethical, democratized development. Licensed under Apache-2.0.

## Installation

1. **Prerequisites**:
   - Python 3.8+ (tested on 3.12).
   - Git (optional for cloning).

2. **Clone the Repo**:
