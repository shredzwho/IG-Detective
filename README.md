# IG-Detective 🕵️‍♂️📸

**Created by [@shredzwho](https://github.com/shredzwho)** | **[💖 Sponsor this project](https://github.com/sponsors/shredzwho)**

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Rich UI](https://img.shields.io/badge/UI-Rich--Aesthetics-brightgreen)](https://github.com/Textualize/rich)

**IG-Detective** is a high-performance, Python-based Open Source Intelligence (OSINT) tool for Instagram. It offers a premium interactive shell to perform deep analysis on Instagram accounts, extract location history, mapping interactions, and generating automated investigative reports.

> [!WARNING]
> **Disclaimer**: This tool is for educational and research purposes only. Use it responsibly and in accordance with Instagram's Terms of Service. The author is not responsible for any misuse.

---

## ⚡ Features

### 🛡️ Evasion & Stealth (Advanced)
- **TLS Fingerprint Spoofing**: Uses a headless Playwright `chromium` browser with `playwright-stealth` to mimic a real environment, completely bypassing Cloudflare and CDN rate-limiting.
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

### 🔬 Research-Driven Forensic Modules (Bleeding-Edge)
- **Account Recovery Enumeration (`recovery`)**: Trigger password reset flow to reveal masked contact tips for administrative email verification.
- **Co-Visitation Analysis (`intersect`)**: Identify physical physical meeting points by cross-referencing GPS/Time intersections between two targets.
- **Stylometry (`stylometry`)**: Generate a digital "Linguistic Signature" to link multiple accounts based on bigram and emoji distribution.
- **Engagement Audit (`audit`)**: Statistical detection of inauthentic bot activity via temporal jitter variance.

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

### 🐳 Run with Docker (Recommended)
You can run IG-Detective entirely within Docker to avoid dependency issues. The container requires an interactive TTY (`-it`) and a volume mount to save your forensic reports.

1. **Using Docker Compose (Easiest)**
   ```bash
   docker-compose run --rm detective
   ```

2. **Using standard Docker**
   ```bash
   docker build -t ig-detective .
   docker run -it -v $(pwd)/data:/app/data ig-detective
   ```

---

## 🛠 Usage

1. **Launch the Shell**
   ```bash
   python3 main.py
   # or use the provided wrapper:
   ./run.sh
   ```

2. **Core Commands**
   Once inside the shell, you must first set a target before running analysis modules:
   
   | Command | Description |
   | :--- | :--- |
   | `target <user>` | Set the investigation target (Required first step) |
   | `info` | View basic profile OSINT (bio, external links, metadata) |
   | `posts` | Fetch the target's recent timeline activity & stats |
   | `addrs` | Extract geographical targets from embedded GPS |
   | `surveillance`| Continuously monitor and trace target metrics/bio changes live |
   | `sna` | Perform Social Network Analysis to map the "Inner Circle" |
   | `temporal`| Calculate timezone and sleep behavior via DBSCAN |
   | `stylometry` | NLP linguistic profiling on captions (Emojis & N-grams) |
   | `help` | Display the interactive help menu |
   | `exit` | Exit the CLI cleanly |

---

## 📑 Detailed Documentation
For a deep dive into the system architecture, forensic methodologies, and evasion logic, see:
👉 **[DOCUMENTATION.md](DOCUMENTATION.md)**

---

## 📂 Project Structure
- `main.py`: Main entrypoint for the shell.
- `run.sh`: Launch wrapper script.
- `src/api/`: Network layer containing the `Playwright` stealth client and auth manager.
- `src/core/`: Foundation layer with data models and config.
- `src/modules/`: Business logic layer with scrapers and deep analytics tools.
- `src/cli/`: Presentation layer with the interactive prompt and Rich formatters.
- `data/`: Automated investigative reports (git-ignored).

---

## 🤝 Contributing
Feel free to fork this project and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

## 📜 License
[MIT]
