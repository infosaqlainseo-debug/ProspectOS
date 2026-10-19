from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/prospectos"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Placeholders for future use
    LLM_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    MOZ_API_KEY: str | None = None
    MOZ_ACCESS_ID: str | None = None
    AHREFS_API_KEY: str | None = None
    SEMRUSH_API_KEY: str | None = None
    MAJESTIC_API_KEY: str | None = None
    SIMILARWEB_API_KEY: str | None = None

    # LLM Settings
    LLM_PROVIDER: str = "openai"  # "openai", "anthropic"
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_MODEL: str = "claude-sonnet-5-5"

    # Outreach & Email Provider Settings
    EMAIL_PROVIDER: str = "none"  # "none", "mock", "gmail", "smtp"
    GMAIL_CLIENT_ID: str | None = None
    GMAIL_CLIENT_SECRET: str | None = None
    GMAIL_REFRESH_TOKEN: str | None = None
    GMAIL_SENDER_EMAIL: str | None = None
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str | None = None
    SMTP_USE_TLS: bool = True
    
    model_config = SettingsConfigDict(env_file=(".env", "backend/.env"), env_file_encoding="utf-8", extra="ignore")

settings = Settings()
