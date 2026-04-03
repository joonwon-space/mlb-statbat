from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    # Comma-separated list of allowed CORS origins.
    # Defaults to localhost dev servers; set to production domain in prod .env.
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    model_config = {"env_file": ".env"}

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a parsed list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
