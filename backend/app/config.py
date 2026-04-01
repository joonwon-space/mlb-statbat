from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://statbat:changeme@db:5432/statbat"
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()
