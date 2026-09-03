from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SpillTrace Backend"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql://spilltrace:spilltrace_local_password@db:5432/spilltrace"
    cors_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()