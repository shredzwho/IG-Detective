from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    # App Config
    APP_NAME: str = "IG-Detective"
    VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Scraping Config
    REQUEST_TIMEOUT: int = 30
    MIN_DELAY: float = 8.0
    MAX_DELAY: float = 15.0
    BATCH_SIZE: int = 50
    BATCH_DELAY_MIN: float = 30.0
    BATCH_DELAY_MAX: float = 60.0

    # Paths
    BASE_DIR: Path = Path.cwd()
    SESSION_DIR: Path = BASE_DIR / "sessions"
    OUTPUT_DIR: Path = BASE_DIR / "output"

    model_config = SettingsConfigDict(env_prefix="IG_DETECTIVE_")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.SESSION_DIR.mkdir(exist_ok=True)
        self.OUTPUT_DIR.mkdir(exist_ok=True)

settings = Settings()
