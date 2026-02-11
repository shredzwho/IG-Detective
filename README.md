# IG-Detective

**Created by [@shredzwho](https://github.com/shredzwho)**

**IG-Detective** is a Python-based Open Source Intelligence (OSINT) tool for Instagram. It offers an **interactive shell** to perform analysis on Instagram accounts, gather information, fetch recent posts, analyze hashtags, and extract contact details in a safe, rate-limited manner.

> ⚠️ **Disclaimer**: This tool is for educational and research purposes only. Use it responsibly and in accordance with Instagram's Terms of Service. The author is not responsible for any misuse.

## Features

- **Interactive Shell**: specific commands to analyze targets (`target`, `info`, `followers`, etc.).
- **Advanced Analysis**: 
    - Fetch detailed profile info.
    - List followers and followings.
    - Analyze most used hashtags from recent posts.
    - View recent posts summaries (likes, comments, captions).
- **Safe Scraping**: 
    - `fwersemail`: Extract emails and phone numbers from followers with built-in **rate limiting** and **batching** to avoid detection.
- **Session Management**: Secure login with 2FA support and session persistence.

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/shredzwho/IG-Detective.git
    cd IG-Detective
    ```

2.  **Create a Virtual Environment** (Optional but Recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the main interactive tool:

```bash
python3 detective.py
```

### Quick Start

1.  **Login**: Enter credentials. Session is saved for future use.
2.  **Set Target**: 
    ```bash
    (ig-detective) target <username>
    ```
3.  **Run Commands**:
    ```bash
    (ig-detective: username) info
    (ig-detective: username) followers 50
    (ig-detective: username) hashtags 20
    ```

### Available Commands

| Command | Description | Usage |
| :--- | :--- | :--- |
| `target` | Set the target username for analysis. | `target <username>` |
| `info` | Show detailed profile information. | `info` |
| `followers` | List followers. | `followers [limit]` |
| `followings` | List users followed by target. | `followings [limit]` |
| `posts` | Show recent posts summary. | `posts [limit]` |
| `hashtags` | Analyze hashtags from recent posts. | `hashtags [limit_posts]` |
| `propic` | Download profile picture. | `propic` |
| `fwersemail` | Scan followers for email/phone (Slow/Safe Mode). | `fwersemail [limit]` |
| `clear` | Clear the screen. | `clear` |
| `logout` | Logout and optionally delete session. | `logout` |
| `exit` | Exit the tool. | `exit` |

### Safety Note on Advanced Scraping

The `fwersemail` command allows you to extract business emails and phone numbers from a target's followers. 
- **Safety First**: This command employs **random delays (10-20s)** and **batch pauses** to prevent your account from being flagged or rate-limited. 
- **Be Patient**: Scanning 50 followers can take 10-15 minutes. This is intentional.

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
