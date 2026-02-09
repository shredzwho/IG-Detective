# IG-Detective

**Created by [@shredzwho](https://github.com/shredzwho)**

**IG-Detective** is a Python-based Open Source Intelligence (OSINT) tool for Instagram. It allows you to gather information, fetch recent posts, and download profiles using a simple command-line interface.

> ⚠️ **Disclaimer**: This tool is for educational and research purposes only. Use it responsibly and in accordance with Instagram's Terms of Service. The author is not responsible for any misuse.

## Features

- **Profile Information**: Fetch details like bio, follower count, following count, and verification status.
- **Recent Posts**: View a summary of the latest posts (captions, likes, comments, dates).
- **Download Profile**: Download all posts and stories from a target profile to your local machine.
- **Session Management**: Securely login with your Instagram account and save the session for future use (supports 2FA).
- **Interactive Menu**: Easy-to-use terminal interface.

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

### Login Options
1.  **Username & Password**: Enter your credentials. Supports Two-Factor Authentication (2FA).
2.  **Session File**: If you've logged in before, the tool saves a session file. Use this option to skip entering credentials.

> **Note**: Logging in is highly recommended as Instagram severely limits anonymous scraping.

### Menu Options
1.  **Get User Profile Info**: Enter a target username to see their profile summary.
2.  **Get Recent Posts**: List the recent posts for a target user.
3.  **Download Profile**: Downloads posts and metadata to a folder named after the user.

## CLI Usage (Advanced)

IG-Detective also includes a direct CLI interface for scripting:

```bash
# Get profile info
python3 src/python/cli.py profile <username>

# Get recent posts
python3 src/python/cli.py posts <username>
```

## Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://choosealicense.com/licenses/mit/)
