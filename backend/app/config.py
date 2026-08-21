"""Configuration. Every value comes from the environment or .env — nothing
sensitive is hardcoded, so this file is safe to commit."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- SMTP ---------------------------------------------------------
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str          # Gmail: an App Password, not your login password
    SMTP_STARTTLS: bool = True  # False if you use port 465 (implicit TLS)

    # --- Addresses ----------------------------------------------------
    # FROM_EMAIL must be an address the SMTP account is allowed to send as,
    # otherwise your mail lands in spam. With Gmail that means SMTP_USER
    # itself, or an alias you have verified in Gmail settings.
    FROM_EMAIL: str
    FROM_NAME: str = "Salman"
    INBOX_EMAIL: str            # where enquiries are delivered to you

    # --- Site ---------------------------------------------------------
    SITE_NAME: str = "salman.dev"
    SITE_URL: str = "https://salman.dev"
    ALLOWED_ORIGINS: str = "https://salman.dev,http://localhost:5500,http://127.0.0.1:8020"

    # --- Abuse control ------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"
    RATE_LIMIT_MAX: int = 3       # submissions allowed...
    RATE_LIMIT_WINDOW: int = 3600 # ...per this many seconds, per IP

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
