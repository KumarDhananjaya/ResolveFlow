"""Application Settings and Configuration using Pydantic Settings."""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """ResolveFlow Enterprise Application Settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application Information
    PROJECT_NAME: str = "ResolveFlow"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = Field(default="development", description="development | staging | production")
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    SECRET_KEY: str = Field(default="dev-secret-key-change-in-prod-resolveflow-aud")

    # Australian Dispute Policies & Financial Thresholds
    CURRENCY: str = "AUD"
    DISPUTE_AUTO_REFUND_THRESHOLD_AUD: float = Field(
        default=100.00,
        description="Transactions above this threshold strictly require Human-in-the-Loop review."
    )
    HIGH_RISK_SCORE_THRESHOLD: int = Field(
        default=70,
        description="Risk score (0-100) above which claims are escalated to human analysts."
    )
    MAX_ALLOWED_CHARGEBACKS_60D: int = Field(
        default=3,
        description="Maximum allowed chargebacks within 60 days before fraud flag is raised."
    )

    # LLM Configuration
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    DEFAULT_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.0

    # PostgreSQL Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/resolveflow",
        description="Async connection string for PostgreSQL."
    )
    DB_ECHO: bool = False

    # Slack Integration (Human-in-the-Loop)
    SLACK_BOT_TOKEN: str = "xoxb-mock"
    SLACK_SIGNING_SECRET: str = "mock-signing-secret"
    SLACK_OPS_CHANNEL: str = "C0123456789"
    SLACK_MOCK_MODE: bool = True

    # Tooling & APIs
    STRIPE_API_KEY: str = "sk_test_mock"
    AUSPOST_API_KEY: str = "mock_auspost_key"

    # Observability
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"


settings = Settings()
