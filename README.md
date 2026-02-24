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

### 🛡️ Evasion & Stealth (Advanced)
- **TLS Fingerprint Spoofing**: Uses `curl_cffi` to impersonate a modern Chrome browser at the network level, bypassing CDN rate-limiting.
- **Poisson Jitter**: Human-like randomized delays between requests to mimic natural user behavior.

### 🔍 Core Reconnaissance
- **User Info**: Comprehensive profile details (ID, Bio, Followers, Business status).
- **Followers/Following**: List and export target's social network.
- **Post Analysis**: Detailed breakdown of recent content, likes, and comments.

### 📍 Advanced OSINT
- **Interactive Geospatial Mapping**: Extracts GPS coordinates from posts and generates a Folium `interactive_map.html` with readable addresses and clickable pins.
- **Social Network Analysis (`sna`)**: Maps interactions to identify the "Inner Circle"—the top 10 users most highly connected to the target.
- **Temporal Activity Profiling (`temporal`)**: Uses DBSCAN clustering to identify the target's "sleep gap" and predict their primary Time Zone.
- **Story Extraction (`stories`)**: Fetch active story URLs.

### 📦 Investigation Management
- **Automated Reporting**: Every command automatically saves results to JSON and TXT reports in `data/<target>/`.
- **Autonomous Batch Mode**: Process multiple targets sequentially from a text file.
- **Intelligent Caching**: Lightning-fast repeated queries via TTL-based caching.

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

2. **Core Commands**
   | Command | Description |
   | :--- | :--- |
   | `target <user>` | Set the investigation target |
   | `info` | Show profile details |
   | `stats` | Get engagement statistics |
   | `addrs` | Extract location history & generate HTML map |
   | `sna` | Perform Social Network Analysis (Inner Circle) |
   | `temporal` | Analyze posting times & predict Time Zone |
   | `batch <file>` | Autonomous processing of multiple handles |
   | `tagged` | Find tagged users |
   | `commenters` | Analyze top interactors |
   | `fwersemail` | Scan followers for contact info (Slow) |
   | `fwingsemail` | Scan followings for contact info (Slow) |
   | `stories` | Fetch active story URLs |

---

## 📂 Project Structure
- `detective.py`: Main interactive shell.
- `src/python/core/scraper.py`: Advanced scraping logic & evasion.
- `src/python/core/analysis.py`: Deep OSINT analysis (SNA, Temporal).
- `src/python/utils/cache.py`: High-performance caching system.
- `data/`: Automated investigative reports (git-ignored).

---

## 🤝 Contributing
Feel free to fork this project and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

## 📜 License
[MIT]
