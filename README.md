# IG-Detective 🕵️‍♂️📸

**Created by [@shredzwho](https://github.com/shredzwho)**

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Rich UI](https://img.shields.io/badge/UI-Rich--Aesthetics-brightgreen)](https://github.com/Textualize/rich)

**IG-Detective** is a high-performance, Python-based Open Source Intelligence (OSINT) tool for Instagram. It offers a premium interactive shell to perform deep analysis on Instagram accounts, extract location history, mapping interactions, and generating automated investigative reports.

> [!WARNING]
> **Disclaimer**: This tool is for educational and research purposes only. Use it responsibly and in accordance with Instagram's Terms of Service. The author is not responsible for any misuse.

---

## ⚡ Features

### 🔍 Core Reconnaissance
- **User Info**: Comprehensive profile details (ID, Bio, Followers, Business status).
- **Followers/Following**: List and export target's social network.
- **Post Analysis**: Detailed breakdown of recent content, likes, and comments.

### 📍 Advanced OSINT (New!)
- **Location History (`addrs`)**: Extract GPS coordinates from posts and reverse-geocode them to readable addresses.
- **Interaction Mapping**:
    - `tagged`: Identify users tagged in the target's posts.
    - `commenters`: Rank followers by engagement level and frequency.
- **Account Statistics (`stats`)**: Detailed aggregate analysis of engagement and media type distribution.
- **Story Extraction (`stories`)**: Fetch active story URLs.

### 📦 Investigation Management
- **Automated Reporting**: Every command automatically saves results to JSON and TXT reports in `data/<target>/`.
- **Intelligent Caching**: Lightning-fast repeated queries via TTL-based caching.
- **Safe Scanning**: Randomized delays and rate-limit management for `fwersemail` and `fwingsemail` commands.

---

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/shredzwho/IG-Detective.git
   cd IG-Detective
   ```

2. **Set up Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🛠 Usage

1. **Launch the Shell**
   ```bash
   python3 detective.py
   ```

2. **Commands**
   | Command | Description |
   | :--- | :--- |
   | `target <user>` | Set the investigation target |
   | `info` | Show profile details |
   | `addrs` | Extract location history |
   | `stats` | Get engagement statistics |
   | `tagged` | Find tagged users |
   | `commenters` | Analyze top interactors |
   | `fwersemail` | Scan followers for contact info (Slow) |
   | `fwingsemail` | Scan followings for contact info (Slow) |
   | `stories` | Fetch active story URLs |

---

## 📂 Project Structure
- `detective.py`: Main interactive shell.
- `src/python/core/scraper.py`: Advanced scraping logic.
- `src/python/core/analysis.py`: Statistical and OSINT analysis.
- `src/python/utils/cache.py`: High-performance caching system.
- `data/`: Automated investigative reports (git-ignored).

---

## 🤝 Contributing
Feel free to fork this project and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

## 📜 License
[MIT]
