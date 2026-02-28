import os
from dataclasses import dataclass

@dataclass
class Config:
    # Storage
    DATA_DIR: str = "data"
    SESSION_DIR: str = os.path.expanduser("~/.config/ig-detective")
    
    # Evasion settings (Poisson distribution means)
    JITTER_MEAN_FAST: float = 3.0
    JITTER_MEAN_NORMAL: float = 8.0
    JITTER_MEAN_SLOW: float = 25.0
    
    # Network settings
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    TIMEOUT: int = 15
    MAX_RETRIES: int = 3
    
    # Cache settings
    CACHE_DEFAULT_TTL: int = 3600 # 1 hour
    
settings = Config()
