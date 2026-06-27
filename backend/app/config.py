"""Application configuration (env-driven, with sane local defaults)."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# repo_root/data  (config.py is at backend/app/config.py)
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DATA_DIR = _REPO_ROOT / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # SQLite by default so the app runs with zero infra. docker-compose overrides
    # this with a PostgreSQL DSN (see docker-compose.yml).
    database_url: str = "sqlite:///./medservice.db"

    # Comma-separated list of allowed CORS origins ("*" for any).
    cors_origins: str = "*"

    # Where services_dictionary.json / clinics.json live.
    data_dir: str = str(_DEFAULT_DATA_DIR)

    # Currency conversion: USD prices are stored converted to KZT (TZ 2.2).
    usd_kzt_rate: float = 470.0

    # TZ 4: data older than this many days must not be presented as "current".
    stale_days: int = 30

    # TZ 4: raw layer retention for audit.
    raw_retention_days: int = 90

    # Fuzzy-match threshold (0-100) for the normalizer. Below this -> unmatched queue.
    match_threshold: int = 86

    # Enable the in-process APScheduler cron (daily reparse). Off by default in dev.
    enable_scheduler: bool = False
    scheduler_cron_hour: int = 3  # 03:00 daily

    # OpenAI (chat assistant). If empty, the assistant uses the deterministic engine.
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"

    @property
    def data_path(self) -> Path:
        return Path(self.data_dir)

    @property
    def cors_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
