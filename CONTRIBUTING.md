# Contributing to IG-Detective 🕵️‍♂️

First off, thank you for considering contributing to IG-Detective! This document outlines the project's architecture, file system, module system, and how the network layer operates to help you get up to speed quickly.

## Requirements

Before developing, ensure you have:
1. Python 3.13+
2. The headless browser dependencies installed via Playwright:
   ```bash
   playwright install chromium
   ```

## 🌳 File System & Architecture

The project has recently been rebuilt from the ground up to follow a strict modular pattern, decoupling the CLI UI from the network scraping logic.

```
project-0sint/
├── main.py                 (Main application entrypoint)
├── run.sh                  (Environment launch wrapper)
├── requirements.txt
├── README.md               (General user documentation)
├── DOCUMENTATION.md        (Deep dive into investigative modules)
├── CONTRIBUTORS.md         (This file)
│
└── src/
    ├── api/                (Network & Evasion Layer)
    │   ├── client.py       (Playwright Stealth Client)
    │   ├── endpoints.py    (Instagram Graph/REST URLs)
    │   └── auth.py         (Session & Cookie Management)
    │
    ├── core/               (Foundation Layer)
    │   ├── models.py       (Pydantic/Dataclass Data Structures: User, Post)
    │   ├── config.py       (Environment constants and rate-limit settings)
    │   ├── cache.py        (Fast local TTL memory cache)
    │   └── exceptions.py   (Standardized error handling)
    │
    ├── modules/            (Business Logic & OSINT Layer)
    │   ├── recon.py        (Profile, Followers, Tagged Data Scrapers)
    │   ├── analytics.py    (SNA, Temporal, Stylometry Processors)
    │   ├── evasion.py      (Poisson Jitter and Request pacing logic)
    │   ├── surveillance.py (Continuous delta-tracking loop)
    │   └── exporter.py     (Mass footprint Zip packaging engine)
    │
    └── cli/                (Presentation Layer)
        ├── shell.py        (cmd2/cmd Interactive Prompt & Routing)
        └── formatters.py   (Rich Tables, Panels, and Output formatting)
```

## ⚙️ The Module System

### 1. The Presentation Layer (`src/cli/`)
The interactive shell is driven by the `cmd` module and utilizes `rich` for all terminal formatting. 
- **Rule**: The CLI layer should **never** make direct HTTP requests. It should only call functions from `src/modules/` and render the returned data structures.

### 2. The Business Logic / OSINT Layer (`src/modules/`)
This layer (`recon.py`, `analytics.py`) contains the logic for pulling data and analyzing it.
- Functions here receive an instance of `InstagramClient`.
- They are responsible for paginating through target data, calling the network client, parsing the raw JSON, and converting it into strict Data Models.
- **Advanced modules** (like SNA or Temporal analysis) operate purely on the defined data models.

### 3. The Foundation Layer (`src/core/`)
Contains all shared definitions. 
- Always define a `dataclass` or `pydantic` model in `models.py` when passing complex objects between the modules and the CLI.
- Standardize your exceptions using `exceptions.py`.

### 4. The Network & Evasion Layer (`src/api/`)
**IG-Detective uses a Headless Browser approach instead of simple HTTP requests.**
Because Instagram heavily utilizes browser fingerprinting to block bots:
- `client.py` uses `playwright` with the `playwright-stealth` plugin.
- It spins up a hidden Chromium instance.
- It injects native Javascript `fetch()` calls into the actual browser page rather than using Python `requests`, perfectly mimicking an organic user's TLS and DOM fingerprints.
- If you need to hit a new endpoint, add the URL format string to `endpoints.py`, and use `client.get_json(url)` or `client.fetch_graphql(...)`. DO NOT bypass `InstagramClient`.

## 🛠️ Code Style & Rules

- **Type Hinting**: All new functions must include Python type hints.
- **Docstrings**: Include clear docstrings for new scrapers indicating what data they retrieve.
- **Rich Output**: If you're adding a new CLI command, ensure its output uses `rich` Tables or Panels. No raw `print()` statements in the shell layer unless unavoidable.
- **Evasion Matters**: If adding a new scraper that paginates aggressively, ensure you utilize the `poisson_jitter()` pacing defined in `src/modules/evasion.py` to prevent the user's account from getting rate-limited.

## Submitting Changes

1. Fork the repo and create your feature branch (`git checkout -b feature/amazing-new-osint-module`).
2. Commit your changes (`git commit -m 'Added cool module'`).
3. Push to the branch (`git push origin feature/amazing-new-osint-module`).
4. Open a Pull Request! We actively review and welcome all forensic contributions.
