from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    test_database_url: str = ""
    migration_database_url: str = ""
    jwt_secret: str
    session_secret: str = ""
    access_token_minutes: int = 30
    refresh_token_days: int = 14
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"
    frontend_url: str = "http://localhost:5173"
    # Comma-separated allowed CORS origins. Falls back to frontend_url when unset.
    # e.g. "https://app.example.com,https://crm.vercel.app,http://localhost:5173"
    cors_origins: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        raw = self.cors_origins or self.frontend_url
        return [o.strip() for o in raw.split(",") if o.strip()]


settings = Settings()
