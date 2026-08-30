"""Validated configuration loaded only at application boundaries."""

from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NUTRITWIN_", env_file=".env", extra="ignore", case_sensitive=False
    )

    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "sqlite+pysqlite:///./nutritwin-dev.db"
    redis_url: str | None = None
    neo4j_uri: str | None = None
    neo4j_user: str | None = None
    neo4j_password: str | None = None
    # Deliberately non-secret local fallback; production_guards rejects it in production.
    jwt_secret: str = "development-only-change-this-secret-32-chars"  # noqa: S105
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_minutes: int = Field(default=15, ge=1, le=60)
    refresh_token_days: int = Field(default=7, ge=1, le=30)
    cors_origins: list[str] = Field(default_factory=list)
    llm_enabled: bool = False
    auto_create_schema: bool = False

    @model_validator(mode="after")
    def production_guards(self) -> Self:
        if self.environment == "production":
            if self.jwt_secret.startswith("development-") or len(self.jwt_secret) < 32:
                raise ValueError("production requires a strong JWT secret")
            if any(origin == "*" for origin in self.cors_origins):
                raise ValueError("wildcard CORS is forbidden in production")
        if self.llm_enabled:
            raise ValueError("LLM adapter is not implemented; keep NUTRITWIN_LLM_ENABLED=false")
        return self


def get_settings() -> Settings:
    return Settings()
