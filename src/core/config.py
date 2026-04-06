from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Smart E-commerce Assistant"
    app_env: str = "development"
    log_level: str = "INFO"
    version: str = "v1"
    max_agent_steps: int = 5

    api_host: str = "127.0.0.1"
    api_port: int = 8000
    streamlit_port: int = 8501

    default_provider: str = "mock"
    default_model: str = "gpt-4o-mini"
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    local_model_path: str = "./models/Phi-3-mini-4k-instruct-q4.gguf"

    postgres_db: str = "lab03"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5432
    database_url: str = "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/lab03"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
